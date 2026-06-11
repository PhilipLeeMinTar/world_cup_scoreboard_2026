package apitest

import (
	"encoding/json"
	"fmt"
	"os"
	"testing"
)

// Suite is the per-test bag of state (env config + global vars + log dir).
// Construct it once per Test* function via New, then call Suite.Run for each
// Case (or just hand-roll Step calls for simple tests).
type Suite struct {
	t          *testing.T
	env        *EnvConfig
	transport  Transport
	jwtToken   string
	logDir     string
	globals    map[string]any
	logStarted map[string]bool
}

// New builds an empty suite tied to t. Call WithEnv/WithEnvFile and
// optionally WithLogDir / WithGlobalVars to configure it before Run.
func New(t *testing.T) *Suite {
	t.Helper()
	return &Suite{t: t, globals: map[string]any{}, logStarted: map[string]bool{}}
}

// WithEnvFile loads a YAML .env file (see resources/env_template.md).
func (s *Suite) WithEnvFile(path string) *Suite {
	s.t.Helper()
	cfg, err := LoadEnv(path)
	if err != nil {
		s.t.Fatalf("apitest: load env: %v", err)
	}
	if err := cfg.Validate(); err != nil {
		s.t.Fatalf("apitest: env: %v", err)
	}
	s.env = cfg
	if s.transport == nil {
		t, err := newTransport(cfg, s.resolvedJWTToken(cfg))
		if err != nil {
			s.t.Fatalf("apitest: transport: %v", err)
		}
		s.transport = t
	}
	return s
}

// WithEnv installs an in-memory env config (useful for tests that build
// EnvConfig programmatically rather than reading from disk).
func (s *Suite) WithEnv(cfg *EnvConfig) *Suite {
	s.t.Helper()
	if err := cfg.Validate(); err != nil {
		s.t.Fatalf("apitest: env: %v", err)
	}
	s.env = cfg
	if s.transport == nil {
		t, err := newTransport(cfg, s.resolvedJWTToken(cfg))
		if err != nil {
			s.t.Fatalf("apitest: transport: %v", err)
		}
		s.transport = t
	}
	return s
}

// WithJWTToken overrides the X-Jwt-Token used to authenticate to paas-gw.
// Default runs should pass the token resolved from APITEST_TOKEN.
func (s *Suite) WithJWTToken(token string) *Suite {
	s.jwtToken = token
	if s.env != nil && isGatewayMode() {
		s.transport = NewGatewayClient(token)
	}
	return s
}

// WithLogDir sets the directory apitest_<case_id>.log will be written into.
func (s *Suite) WithLogDir(dir string) *Suite {
	s.logDir = dir
	return s
}

// WithGlobalVars merges in suite-level variables. Lower precedence than
// case-level Vars and step-level Extracted variables.
func (s *Suite) WithGlobalVars(vars map[string]any) *Suite {
	for k, v := range vars {
		s.globals[k] = v
	}
	return s
}

// Run executes every Step in c, gating PASS/FAIL through testing.T.
// Each step becomes a t.Run subtest, so `go test -v` produces a tree mirror
// of the case structure.
func (s *Suite) Run(c Case) {
	s.t.Helper()
	if s.env == nil {
		s.t.Fatalf("apitest: suite missing env config (call WithEnvFile or WithEnv first)")
	}
	if s.transport == nil {
		t, err := newTransport(s.env, s.resolvedJWTToken(s.env))
		if err != nil {
			s.t.Fatalf("apitest: transport: %v", err)
		}
		s.transport = t
	}
	if c.ID == "" {
		c.ID = c.Name
	}

	ctx := newContext(s.globals, c.Vars)

	for _, step := range c.Steps {
		step := step // capture loop var
		s.t.Run(step.Name, func(t *testing.T) {
			s.runStep(t, c.ID, step, ctx, c.Type)
		})
	}
}

// RunStep runs a single ad-hoc step (no Case wrapper). Returns the
// StepResult so callers can do follow-up assertions in Go directly.
func (s *Suite) RunStep(caseID string, step Step, vars map[string]any) StepResult {
	s.t.Helper()
	if s.env == nil {
		s.t.Fatalf("apitest: suite missing env config (call WithEnvFile or WithEnv first)")
	}
	if s.transport == nil {
		t, err := newTransport(s.env, s.resolvedJWTToken(s.env))
		if err != nil {
			s.t.Fatalf("apitest: transport: %v", err)
		}
		s.transport = t
	}
	ctx := newContext(s.globals, vars)
	return s.runStep(s.t, caseID, step, ctx, "")
}

// runStep is the shared execution body for both Run and RunStep.
func (s *Suite) runStep(t *testing.T, caseID string, step Step, ctx *context, defaultType string) StepResult {
	t.Helper()

	stepType := step.Type
	if stepType == "" {
		stepType = defaultType
	}
	if stepType == "" {
		stepType = "HTTP"
	}

	resolvedHeaders := resolveStringMap(step.Headers, ctx)
	resolvedParams := resolveStringMap(step.Params, ctx)
	resolvedRpcContext := resolveStringMap(step.RpcContext, ctx)
	resolvedBody := resolveValue(step.Body, ctx)

	merged := injectHeaders(stepType, resolvedHeaders, s.env.TestAccount)

	bodyStr, err := serializeBody(resolvedBody)
	if err != nil {
		t.Fatalf("apitest: serialize body: %v", err)
	}

	resolvedStep := step
	resolvedStep.Headers = merged
	resolvedStep.Params = resolvedParams
	resolvedStep.RpcContext = resolvedRpcContext
	routeEnv, err := s.env.ResolveService(resolvedStep.Service)
	if err != nil {
		t.Errorf("apitest[%s]: resolve service: %v", step.Name, err)
		return StepResult{Name: step.Name, Status: "ERROR", ErrMessage: err.Error()}
	}

	var call *gatewayCallResult
	pathMode := PathModeHTTP
	switch stepType {
	case "RPC":
		pathMode = PathModeRPC
		call, err = s.transport.SendRPC(routeEnv, resolvedStep, merged, resolvedRpcContext, bodyStr)
	default:
		call, err = s.transport.SendHTTP(routeEnv, resolvedStep, merged, bodyStr)
	}
	if err != nil {
		t.Errorf("apitest[%s]: transport error: %v", step.Name, err)
		return StepResult{Name: step.Name, Status: "ERROR", ErrMessage: err.Error()}
	}

	// Persist log (best-effort).
	appendLog := s.logStarted[caseID]
	s.logStarted[caseID] = true
	if logErr := writeCaseLog(s.logDir, caseID, resolvedStep, call, appendLog); logErr != nil {
		t.Logf("apitest: log write failed: %v", logErr)
	}

	// Extract before assertions so subsequent assertions can also see them.
	extracted := extractAll(call.Body, step.Extract, pathMode)
	for k, v := range extracted {
		ctx.setExtracted(k, v)
	}

	// Resolve the effective business status code for assertions.
	// When the gateway successfully proxied the downstream response,
	// use BusinessCode (the downstream service's own status code).
	// Otherwise fall back to the gateway's HTTP status code.
	businessStatusCode := call.StatusCode
	if call.BusinessCode != 0 {
		businessStatusCode = call.BusinessCode
	}

	// Run assertions.
	asserts := evaluateAll(step.Asserts, businessStatusCode, call.Body, pathMode)
	allPassed := true
	for _, a := range asserts {
		if !a.Passed {
			allPassed = false
			if a.Err != nil {
				t.Errorf("assert %q failed: %v", a.Expression, a.Err)
			} else {
				t.Errorf("assert %q failed (actual=%v)", a.Expression, a.Actual)
			}
		}
	}

	// Implicit gateway-level checks: HTTP 200 + has_permission == true.
	if call.StatusCode != 200 {
		allPassed = false
		t.Errorf("gateway HTTP status %d", call.StatusCode)
	}
	if !call.HasPermission {
		allPassed = false
		t.Errorf("gateway has_permission=false")
	}

	status := "PASSED"
	if !allPassed {
		status = "FAILED"
	}

	return StepResult{
		Name:       step.Name,
		Status:     status,
		StatusCode: businessStatusCode,
		PathMode:   pathMode,
		Body:       call.Body,
		Headers:    call.Headers,
		LatencyMs:  call.LatencyMs,
		Asserts:    asserts,
		Extracted:  extracted,
	}
}

// resolveStringMap walks a string->string map and runs each value through
// resolveString, then stringifies non-string results so the resulting map
// remains string->string (HTTP headers / query params can't carry typed values).
func resolveStringMap(in map[string]string, c *context) map[string]string {
	if in == nil {
		return nil
	}
	out := make(map[string]string, len(in))
	for k, v := range in {
		r := resolveString(v, c)
		out[k] = fmt.Sprint(r)
	}
	return out
}

// serializeBody handles request bodies: maps/structs -> JSON, strings pass
// through verbatim, nil -> empty string.
func serializeBody(b any) (string, error) {
	if b == nil {
		return "", nil
	}
	if s, ok := b.(string); ok {
		return s, nil
	}
	raw, err := json.Marshal(b)
	if err != nil {
		return "", err
	}
	return string(raw), nil
}

func envToken(cfg *EnvConfig) string {
	if token := os.Getenv("APITEST_TOKEN"); token != "" {
		return token
	}
	return ""
}

func (s *Suite) resolvedJWTToken(cfg *EnvConfig) string {
	if s.jwtToken != "" {
		return s.jwtToken
	}
	return envToken(cfg)
}

// JSON is an alias for map[string]any to make Step.Body literals lighter
// to type in tests:
//
//	Body: apitest.JSON{"name": "${{user_name}}"}
type JSON = map[string]any
