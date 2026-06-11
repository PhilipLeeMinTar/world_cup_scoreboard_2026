package apitest

import (
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

// Env is the concise public name used by human-written tests.
type Env = EnvConfig

// TestContext is the flat, Tesla-Go-like entry point for generated cases.
// It keeps gateway/env/log state out of the test body while still allowing
// tests to read like: req -> Call -> Assert.
type TestContext struct {
	t       *testing.T
	suite   *Suite
	caseID  string
	vars    map[string]any
	auth    *AuthConfig
	specDir string
}

// HTTPRequest describes one HTTP call through paas-gw.
type HTTPRequest struct {
	Name       string
	Service    string
	Method     string
	Path       string
	Headers    map[string]string
	Params     map[string]string
	Body       any
	Extract    map[string]string
	RpcContext map[string]string
}

// RPCRequest describes one RPC call through paas-gw.
type RPCRequest struct {
	Name       string
	Service    string
	Method     string
	Headers    map[string]string
	RpcContext map[string]string
	Body       any
	Extract    map[string]string
}

// Response is the public result returned by CallHTTP/CallRPC.
type Response struct {
	StepResult
}

// NewContextFromSpec is the only public entry point for generated tests. It
// resolves all configuration purely from disk relative to the spec directory
// hard-coded into the generated *_test.go file:
//
//	specDir/.env       -> routing fields (flat psm/host/env/... or services.<name>)
//	specDir/auth.yaml  -> business auth headers per profile (optional)
//	specDir/api_test_logs/  -> per-case log output
//
// specDir must be an absolute path. Generated tests compute it via
// runtime.Caller(0) + a relative path, so the same code runs unchanged after
// any clone/checkout. Only APITEST_TOKEN (paas-gw JWT) remains as an env var,
// because it is per-user, time-limited, and unsuitable for git-tracked files.
func NewContextFromSpec(t *testing.T, specDir string) *TestContext {
	t.Helper()
	if specDir == "" {
		t.Fatalf("apitest: NewContextFromSpec requires a non-empty specDir")
	}
	if !filepath.IsAbs(specDir) {
		t.Fatalf("apitest: specDir must be absolute, got %q", specDir)
	}
	if info, err := os.Stat(specDir); err != nil || !info.IsDir() {
		t.Fatalf("apitest: specDir %q does not exist or is not a directory", specDir)
	}

	envPath := filepath.Join(specDir, ".env")
	cfg, err := LoadEnv(envPath)
	if err != nil {
		t.Fatalf("apitest: load env %q: %v", envPath, err)
	}
	if err := cfg.Validate(); err != nil {
		t.Fatalf("apitest: env %q: %v", envPath, err)
	}

	authPath := filepath.Join(specDir, "auth.yaml")
	auth, err := LoadAuth(authPath)
	if err != nil {
		t.Fatalf("apitest: load auth %q: %v", authPath, err)
	}

	token := os.Getenv("APITEST_TOKEN")
	if token == "" && isGatewayMode() {
		t.Skip("paas-gw JWT not set; run user_jwt in the workflow or export APITEST_TOKEN=<jwt>")
	}

	logDir := filepath.Join(specDir, "api_test_logs")
	_ = os.MkdirAll(logDir, 0o755)

	suite := New(t).WithEnv(cfg).WithLogDir(logDir)
	if isGatewayMode() {
		suite = suite.WithJWTToken(token)
	}
	return &TestContext{
		t:       t,
		suite:   suite,
		caseID:  safeCaseID(t.Name()),
		vars:    map[string]any{},
		auth:    auth,
		specDir: specDir,
	}
}

// WithCaseID overrides the log case id used by CallHTTP/CallRPC.
func (c *TestContext) WithCaseID(id string) *TestContext {
	c.caseID = id
	return c
}

// WithVars adds variables available to later request bodies/params via
// ${{var}} or ${var} placeholders.
func (c *TestContext) WithVars(vars map[string]any) *TestContext {
	for k, v := range vars {
		c.vars[k] = v
	}
	return c
}

// DeferCleanup registers cleanup tied to the active test case.
func (c *TestContext) DeferCleanup(fn func()) {
	c.t.Cleanup(fn)
}

// Env returns the underlying *EnvConfig loaded from <specDir>/.env, so
// generated tests can pass it to helpers like apitest.Sample(t, env, key, ...)
// without re-reading the file.
func (c *TestContext) Env() *EnvConfig {
	if c.suite == nil {
		return nil
	}
	return c.suite.env
}

// EnvFor returns the single-service routing view for service. Empty service
// returns the default service. This is useful when generated tests need
// env-specific samples for a non-default downstream service.
func (c *TestContext) EnvFor(service string) *EnvConfig {
	c.t.Helper()
	if c.suite == nil || c.suite.env == nil {
		return nil
	}
	env, err := c.suite.env.ResolveService(service)
	if err != nil {
		c.t.Fatalf("apitest: %v", err)
	}
	return env
}

// AuthHeaders returns the business auth headers for the current case, selected
// per the auth.yaml resolution rules:
//
//  1. case_profiles[caseID] when configured
//  2. profiles["default"] otherwise
//  3. empty map when auth.yaml is absent (no business auth needed)
//
// Generated tests use this as the default for HTTPRequest.Headers; auth values
// never appear inline in *_test.go.
func (c *TestContext) AuthHeaders() map[string]string {
	c.t.Helper()
	h, err := c.auth.HeadersFor(c.caseID, "")
	if err != nil {
		c.t.Fatalf("apitest: %v", err)
	}
	return h
}

// AuthHeadersFor returns the business auth headers for an explicit profile
// (overrides case_profiles). Use this for cases that intentionally exercise a
// different identity than the default mapping (e.g. privilege escalation,
// admin-vs-user comparison). An undefined profile name is fatal.
func (c *TestContext) AuthHeadersFor(profile string) map[string]string {
	c.t.Helper()
	h, err := c.auth.HeadersFor(c.caseID, profile)
	if err != nil {
		c.t.Fatalf("apitest: %v", err)
	}
	return h
}

// CallHTTP executes one HTTP request and returns its response.
func CallHTTP(ctx *TestContext, req HTTPRequest) Response {
	ctx.t.Helper()
	name := req.Name
	if name == "" {
		name = strings.TrimSpace(req.Method + " " + req.Path)
	}
	res := ctx.suite.RunStep(ctx.caseID, Step{
		Name:       name,
		Type:       "HTTP",
		Service:    req.Service,
		API:        req.Path,
		Method:     req.Method,
		Headers:    req.Headers,
		Params:     req.Params,
		RpcContext: req.RpcContext,
		Body:       req.Body,
		Extract:    req.Extract,
	}, ctx.vars)
	mergeExtracted(ctx.vars, res.Extracted)
	return Response{StepResult: res}
}

// CallRPC executes one RPC request and returns its response.
func CallRPC(ctx *TestContext, req RPCRequest) Response {
	ctx.t.Helper()
	name := req.Name
	if name == "" {
		name = req.Method
	}
	res := ctx.suite.RunStep(ctx.caseID, Step{
		Name:       name,
		Type:       "RPC",
		Service:    req.Service,
		API:        req.Method,
		Headers:    req.Headers,
		RpcContext: req.RpcContext,
		Body:       req.Body,
		Extract:    req.Extract,
	}, ctx.vars)
	mergeExtracted(ctx.vars, res.Extracted)
	return Response{StepResult: res}
}

// Assert evaluates response expressions using the same grammar as Step.Asserts.
func Assert(t *testing.T, resp Response, expressions ...string) {
	t.Helper()
	asserts := evaluateAll(expressions, resp.StatusCode, resp.Body, effectivePathMode(resp.PathMode))
	for _, a := range asserts {
		if a.Passed {
			continue
		}
		if a.Err != nil {
			t.Errorf("assert %q failed: %v", a.Expression, a.Err)
		} else {
			t.Errorf("assert %q failed (actual=%v)", a.Expression, a.Actual)
		}
	}
}

// Value extracts a JSONPath value from the response body.
func (r Response) Value(path string) any {
	v, _ := jsonPathExtractWithMode(r.Body, path, effectivePathMode(r.PathMode))
	return v
}

// ExtractString extracts a JSONPath value and stringifies it for ordinary Go
// variable passing between calls.
func (r Response) ExtractString(path string) string {
	v := r.Value(path)
	if v == nil {
		return ""
	}
	return fmt.Sprint(v)
}

// ExtractInt64 extracts a JSONPath value as int64 when possible.
func (r Response) ExtractInt64(path string) int64 {
	switch v := r.Value(path).(type) {
	case int:
		return int64(v)
	case int64:
		return v
	case float64:
		return int64(v)
	default:
		return 0
	}
}

// T returns the active testing.T for suite-style tests.
func (s *Suite) T() *testing.T {
	return s.t
}

// Assert lets suite methods use s.Assert(resp, "...") without passing t around.
func (s *Suite) Assert(resp Response, expressions ...string) {
	Assert(s.t, resp, expressions...)
}

// DeferCleanup registers cleanup tied to the active suite case.
func (s *Suite) DeferCleanup(fn func()) {
	s.t.Cleanup(fn)
}

// RunSuite runs Tesla-Go-style suite tests. It recognizes optional lifecycle
// methods named SuiteSetup, SuiteTeardown, CaseSetup and CaseTeardown.
func RunSuite(t *testing.T, suite any) {
	t.Helper()
	setEmbeddedSuite(t, suite)
	callNoArg(suite, "SuiteSetup")
	defer callNoArg(suite, "SuiteTeardown")

	v := reflect.ValueOf(suite)
	typ := v.Type()
	suiteName := strings.TrimPrefix(typ.Elem().Name(), "*")
	for i := 0; i < typ.NumMethod(); i++ {
		method := typ.Method(i)
		if !strings.HasPrefix(method.Name, "Test") || method.Type.NumIn() != 1 {
			continue
		}
		testName := method.Name
		t.Run(testName, func(st *testing.T) {
			setEmbeddedSuite(st, suite)
			callLifecycle(suite, "CaseSetup", suiteName, testName)
			defer callLifecycle(suite, "CaseTeardown", suiteName, testName)
			method.Func.Call([]reflect.Value{v})
		})
	}
}

func setEmbeddedSuite(t *testing.T, suite any) {
	v := reflect.ValueOf(suite)
	if v.Kind() != reflect.Pointer || v.Elem().Kind() != reflect.Struct {
		t.Fatalf("apitest: RunSuite requires pointer to struct, got %T", suite)
	}
	field := v.Elem().FieldByName("Suite")
	if !field.IsValid() || !field.CanSet() {
		t.Fatalf("apitest: suite %T must embed apitest.Suite", suite)
	}
	next := *New(t)
	if existing, ok := field.Addr().Interface().(*Suite); ok {
		next.env = existing.env
		next.transport = existing.transport
		next.jwtToken = existing.jwtToken
		next.logDir = existing.logDir
		next.globals = cloneVarMap(existing.globals)
	}
	field.Set(reflect.ValueOf(next))
}

func callNoArg(receiver any, name string) {
	m := reflect.ValueOf(receiver).MethodByName(name)
	if m.IsValid() && m.Type().NumIn() == 0 {
		m.Call(nil)
	}
}

func callLifecycle(receiver any, name, suiteName, testName string) {
	m := reflect.ValueOf(receiver).MethodByName(name)
	if m.IsValid() && m.Type().NumIn() == 2 {
		m.Call([]reflect.Value{reflect.ValueOf(suiteName), reflect.ValueOf(testName)})
	}
}

func effectivePathMode(mode PathMode) PathMode {
	if mode == "" {
		return PathModeRPC
	}
	return mode
}

func mergeExtracted(vars map[string]any, extracted map[string]any) {
	for k, v := range extracted {
		vars[k] = v
	}
}

func safeCaseID(name string) string {
	name = strings.ReplaceAll(name, "/", "_")
	name = strings.ReplaceAll(name, " ", "_")
	return name
}
