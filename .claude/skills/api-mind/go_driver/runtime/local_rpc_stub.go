package apitest

import "fmt"

// NewLocalRPCTransport is implemented by repo-specific overlay local_rpc.go.
// The skill baseline ships this stub so transport.go compiles; repositories
// that support APITEST_MODE=local_rpc replace this file with a Kitex client
// implementation for their service PSM.
func NewLocalRPCTransport(cfg *EnvConfig) (Transport, error) {
	_ = cfg
	return nil, fmt.Errorf("APITEST_MODE=local_rpc requires repo overlay tests/integration/apitest/local_rpc.go implementing NewLocalRPCTransport; see runtime/README.md")
}
