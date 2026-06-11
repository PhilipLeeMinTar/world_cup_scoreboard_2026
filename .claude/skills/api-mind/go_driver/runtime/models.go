// Package apitest is the Go runtime for paas-gw based API integration tests.
//
//	parse env -> resolve variables -> build paas-gw payload -> POST gateway
//	  -> parse downstream response -> evaluate assertions -> extract variables
//	  -> write apitest_<case_id>.log
//
// The library is intentionally small: a Suite owns the env / token / log dir
// and each Case is a slice of Steps run as t.Run subtests. See README.md for
// usage and the api-mind skill (`apitest.md`) for the generation contract.
package apitest

// Step is a single HTTP/RPC call inside a Case.
//
// For HTTP, fill API/Method (Body and Params optional).
// For RPC, set Type=RPC and put RPC method name into API.
type Step struct {
	Type    string            // "HTTP" (default) or "RPC"
	Name    string            // human readable step name (used in t.Run)
	Service string            // optional service key in EnvConfig.Services; empty uses default_service
	API     string            // HTTP path with optional ?query, or RPC method name
	Method  string            // HTTP method (GET/POST/...); ignored for RPC
	Headers map[string]string // step-level headers (merged on top of env headers)
	// RpcContext carries Kitex metainfo persistent values for RPC steps.
	// Keys here are sent to paas-gw as `rpc_context: [{key,value,type:"persistent",status:0}]`
	// and become metainfo persistent values on the downstream RPC, which is the
	// only channel that triggers BAM mock dyeing. Putting these into Headers
	// instead would make paas-gw send them as ordinary RPC headers and the
	// mesh sidecar would NOT see them. Ignored for HTTP steps.
	//
	// Typical mock dyeing keys: MOCK_TAG, DYECP_FD_MOCK.
	RpcContext map[string]string
	Params     map[string]string // appended as query string for HTTP
	Body       any               // map / struct / string; serialized as JSON when not string
	Extract    map[string]string // var_name -> JSONPath expression
	Asserts    []string          // assertion expressions (see assert.go grammar)
	// Purpose is an optional description echoed into logs/reports.
	Purpose string
}

// Case is a logical test scenario consisting of one or more sequential steps.
//
// Variables resolution precedence (highest first):
//
//	extracted (set by previous Step.Extract) > Vars > GlobalVars
type Case struct {
	ID         string
	Name       string
	Priority   string         // P0/P1/P2; informational only (go test ordering uses t.Run)
	Type       string         // default request type when Step.Type is empty
	Vars       map[string]any // case-level variables
	GlobalVars map[string]any // suite-level variables
	Steps      []Step
}

// ServiceConfig is one routing target inside EnvConfig. Fields are bound
// together: psm/host/env/branch/zone/idc/cluster describe the same downstream
// service and must be selected as a unit.
type ServiceConfig struct {
	PSM     string `yaml:"psm"`
	Host    string `yaml:"host"`
	Env     string `yaml:"env"`
	Branch  string `yaml:"branch"`
	Zone    string `yaml:"zone"`
	IDC     string `yaml:"idc"`
	Cluster string `yaml:"cluster"`
}

// EnvConfig is the parsed `.env` file (YAML list/dict) used to drive gateway
// routing. The legacy flat fields are retained for old `.env` files and helper
// compatibility; new multi-PSM configs should use DefaultService + Services.
// TestAccount is retained only for legacy `.env` files; newly generated tests
// should put business auth headers in code-level Headers.
type EnvConfig struct {
	PSM            string                   `yaml:"psm"`
	Host           string                   `yaml:"host"`
	Env            string                   `yaml:"env"`
	Branch         string                   `yaml:"branch"`
	Zone           string                   `yaml:"zone"`
	IDC            string                   `yaml:"idc"`
	Cluster        string                   `yaml:"cluster"`
	DefaultService string                   `yaml:"default_service"`
	Services       map[string]ServiceConfig `yaml:"services"`
	TestAccount    map[string]string        `yaml:"test_account"` // legacy only; do not emit in generated .env
}

// AssertResult records the outcome of a single assertion expression.
type AssertResult struct {
	Expression string
	Passed     bool
	Actual     any
	Err        error
}

// PathMode selects JSONPath resolution rules for HTTP AGW envelopes vs raw RPC bodies.
type PathMode string

const (
	PathModeHTTP PathMode = "HTTP"
	PathModeRPC  PathMode = "RPC"
)

// StepResult is the recorded outcome of executing one Step.
type StepResult struct {
	Name       string
	Status     string // PASSED / FAILED / ERROR
	StatusCode int
	PathMode   PathMode
	Body       any
	Headers    map[string]string
	LatencyMs  float64
	Asserts    []AssertResult
	Extracted  map[string]any
	ErrMessage string
}
