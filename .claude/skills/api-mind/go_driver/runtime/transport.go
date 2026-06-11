package apitest

import (
	"fmt"
	"os"
	"strings"
)

const (
	transportModeGateway  = "gateway"
	transportModeLocalRPC = "local_rpc"
)

// Transport is the execution backend behind CallHTTP/CallRPC.
//
// The generated test code stays stable while the runtime can choose a gateway
// backend or a local Kitex backend based on APITEST_MODE.
type Transport interface {
	SendHTTP(cfg *EnvConfig, step Step, headers map[string]string, body string) (*gatewayCallResult, error)
	SendRPC(cfg *EnvConfig, step Step, headers, rpcContext map[string]string, body string) (*gatewayCallResult, error)
}

func newTransport(cfg *EnvConfig, jwtToken string) (Transport, error) {
	switch resolveTransportMode() {
	case transportModeGateway:
		return NewGatewayClient(jwtToken), nil
	case transportModeLocalRPC:
		return NewLocalRPCTransport(cfg)
	default:
		return nil, fmt.Errorf("unsupported APITEST_MODE %q (supported: %s, %s)", os.Getenv("APITEST_MODE"), transportModeGateway, transportModeLocalRPC)
	}
}

func resolveTransportMode() string {
	mode := strings.TrimSpace(strings.ToLower(os.Getenv("APITEST_MODE")))
	if mode == "" {
		return transportModeGateway
	}
	return mode
}

func isGatewayMode() bool {
	return resolveTransportMode() == transportModeGateway
}
