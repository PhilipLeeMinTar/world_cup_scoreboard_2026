package apitest

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// Default paas-gw endpoints. The domains follow the Explorer OpenAPI control
// plane table and are selected inside the gateway layer from zone/idc/env.
const (
	CNGatewayURL      = "https://paas-gw.byted.org/api/v1"
	BOEGatewayURL     = "https://paas-gw-boe.byted.org/api/v1"
	I18NGatewayURL    = "https://bc-useastdt-gw.tiktok-row.net/api/v1"
	BOEI18NGatewayURL = "https://paas-gw-boei18n.byted.org/api/v1"
	GCPGatewayURL     = "https://paas-gw-gcp.tiktoke.org/api/v1"
	TTPGatewayURL     = "https://paas-gw-tx.tiktokd.org/api/v1"
	SINFBOEGatewayURL = "https://paas-gw-boe.sinf.net/api/v1"
	SINFGatewayURL    = "https://paas-gw.sinf.net/api/v1"

	defaultBAMPSMCluster    = 2 // I18N
	defaultRequestTimeoutMs = 10_000
)

// GatewayClient sends test payloads to paas-gw and returns the parsed envelope.
type GatewayClient struct {
	httpClient *http.Client
	jwtToken   string
}

// NewGatewayClient builds a client with sane defaults (30s read timeout).
// Override timeout by replacing httpClient if needed.
func NewGatewayClient(jwtToken string) *GatewayClient {
	return &GatewayClient{
		httpClient: &http.Client{Timeout: 60 * time.Second},
		jwtToken:   jwtToken,
	}
}

// rpcContextItem is one entry inside paas-gw's `rpc_context` array, the
// official channel for declaring Kitex metainfo persistent values on an RPC
// step. type=="persistent" is required for BAM mock dyeing to take effect;
// regular HTTP/RPC headers in the `header` field do NOT enter the metainfo
// channel and therefore do NOT trigger mock interception.
type rpcContextItem struct {
	Key    string `json:"key"`
	Value  string `json:"value"`
	Type   string `json:"type"`   // always "persistent" for our use cases
	Status int    `json:"status"` // 0 = enabled
}

// gatewayRequest is the JSON payload paas-gw expects on /http_request and
// /rpc_request. Field names are exactly what the gateway parses; renaming any
// of them will silently break the call.
type gatewayRequest struct {
	Env            string            `json:"env,omitempty"`
	Header         map[string]string `json:"header,omitempty"`
	RpcContext     []rpcContextItem  `json:"rpc_context,omitempty"`
	Request        string            `json:"request,omitempty"`
	Method         string            `json:"method,omitempty"`
	Path           string            `json:"path,omitempty"`
	FuncName       string            `json:"func_name,omitempty"`
	BAMPSMCluster  int               `json:"bam_psm_cluster"`
	PSM            string            `json:"psm,omitempty"`
	Host           string            `json:"host,omitempty"`
	Zone           string            `json:"zone,omitempty"`
	IDC            string            `json:"idc,omitempty"`
	Cluster        string            `json:"cluster,omitempty"`
	Serialization  string            `json:"serialization,omitempty"`
	RequestTimeout int               `json:"request_timeout,omitempty"`
	ConnectTimeout int               `json:"connect_timeout,omitempty"`
	IDLSource      int               `json:"idl_source,omitempty"`
	IDLVersion     string            `json:"idl_version,omitempty"`
	Branch         string            `json:"branch,omitempty"`
}

// buildRpcContext converts a key/value map into the array form paas-gw expects
// in `rpc_context`. All entries are flagged persistent so they propagate to
// downstream RPCs through Kitex metainfo (the channel BAM mesh dyeing reads).
func buildRpcContext(kv map[string]string) []rpcContextItem {
	if len(kv) == 0 {
		return nil
	}
	out := make([]rpcContextItem, 0, len(kv))
	for k, v := range kv {
		out = append(out, rpcContextItem{
			Key:    k,
			Value:  v,
			Type:   "persistent",
			Status: 0,
		})
	}
	return out
}

// gatewayResponse models the relevant pieces of paas-gw's envelope. Unknown
// fields are tolerated.
type gatewayResponse struct {
	Data        json.RawMessage   `json:"data"`
	RespHeaders map[string]string `json:"resp_headers"`
	LogID       string            `json:"log_id"`
	StatusCode  int               `json:"status_code"`
	ErrorCode   int               `json:"error_code"`
	HasPerm     *bool             `json:"has_permission,omitempty"`
}

// SendHTTP sends an HTTP-style step through the gateway and returns the
// downstream response decoded as a Go value, plus the raw gateway envelope
// (used by the logger to write the runtime block).
func (g *GatewayClient) SendHTTP(cfg *EnvConfig, step Step, headers map[string]string, body string) (*gatewayCallResult, error) {
	payload := gatewayRequest{
		Env:           cfg.Env,
		Header:        headers,
		Request:       body,
		Method:        strings.ToUpper(step.Method),
		Path:          appendQuery(step.API, step.Params),
		BAMPSMCluster: defaultBAMPSMCluster,
		PSM:           cfg.PSM,
		Host:          cfg.Host,
		Zone:          cfg.Zone,
		IDC:           strings.ToLower(cfg.IDC),
		Cluster:       cfg.Cluster,
		IDLVersion:    cfg.Branch,
	}
	// When both psm and zone are set, host is dropped (psm+zone wins).
	if payload.PSM != "" && payload.Zone != "" {
		payload.Host = ""
	}
	endpoint := g.endpoint(cfg, "http_request")
	return g.send(endpoint, payload, true, step, cfg)
}

// SendRPC sends an RPC-style step via paas-gw /rpc_request.
//
// Note: /rpc_request requires `branch` (the IDL branch). HTTP requests use
// `idl_version` instead. Don't conflate the two — the gateway's binder will
// reject with "missing required parameter" otherwise.
//
// rpcContext carries Kitex metainfo persistent values (e.g. BAM mock dyeing
// headers MOCK_TAG / DYECP_FD_MOCK). It must NOT be folded into headers — the
// mesh sidecar only reads metainfo via paas-gw's `rpc_context` field.
func (g *GatewayClient) SendRPC(cfg *EnvConfig, step Step, headers, rpcContext map[string]string, body string) (*gatewayCallResult, error) {
	payload := gatewayRequest{
		Env:           cfg.Env,
		Header:        headers,
		RpcContext:    buildRpcContext(rpcContext),
		Request:       body,
		FuncName:      step.API,
		PSM:           cfg.PSM,
		Branch:        cfg.Branch,
		BAMPSMCluster: defaultBAMPSMCluster,
		Zone:          cfg.Zone,
		IDC:           strings.ToLower(cfg.IDC),
		Cluster:       cfg.Cluster,
	}
	endpoint := g.endpoint(cfg, "rpc_request")
	return g.send(endpoint, payload, false, step, cfg)
}

// gatewayCallResult is the post-decode summary one Step produces, including
// everything the logger and assertion engine need.
type gatewayCallResult struct {
	StatusCode       int
	HasPermission    bool
	BusinessCode     int
	GatewayErrorCode int
	Body             any // downstream response, decoded
	Headers          map[string]string
	LogIDDownstream  string
	LatencyMs        float64
	GatewayURL       string
	GatewayLogID     string
	GatewayBody      any
	BusinessCurl     string
	GatewayCurl      string
	Timestamp        string
}

func (g *GatewayClient) endpoint(cfg *EnvConfig, kind string) string {
	return gatewayBaseURL(cfg) + "/" + kind
}

func gatewayBaseURL(cfg *EnvConfig) string {
	switch resolveControlPlane(cfg) {
	case "cn":
		return CNGatewayURL
	case "boe":
		return BOEGatewayURL
	case "boei18n", "boettp":
		return BOEI18NGatewayURL
	case "gcp":
		return GCPGatewayURL
	case "ttp", "ttp2", "tx":
		return TTPGatewayURL
	case "sinf-boe":
		return SINFBOEGatewayURL
	case "sinf":
		return SINFGatewayURL
	default:
		return I18NGatewayURL
	}
}

func resolveControlPlane(cfg *EnvConfig) string {
	if cfg == nil {
		return "i18n"
	}
	zone := strings.ToLower(cfg.Zone)
	idc := strings.ToLower(cfg.IDC)
	env := strings.ToLower(cfg.Env)
	switch {
	case strings.Contains(zone, "ttp-boe") || strings.Contains(idc, "boettp"):
		return "boettp"
	case strings.Contains(zone, "us-boe") || strings.Contains(zone, "boei18n") || strings.Contains(idc, "boei18n"):
		return "boei18n"
	case strings.Contains(zone, "china-boe") || idc == "boe" || idc == "cof" || strings.HasPrefix(env, "boe"):
		return "boe"
	case strings.Contains(zone, "us-ttp") || strings.Contains(zone, "eu-ttp") || strings.Contains(idc, "ttp") || strings.Contains(idc, "useast5"):
		return "ttp"
	case strings.Contains(zone, "china") || zone == "cn":
		return "cn"
	case strings.Contains(zone, "gcp"):
		return "gcp"
	case strings.Contains(zone, "sinf") && strings.Contains(zone, "boe"):
		return "sinf-boe"
	case strings.Contains(zone, "sinf"):
		return "sinf"
	default:
		return "i18n"
	}
}

func (g *GatewayClient) send(endpoint string, payload gatewayRequest, isHTTP bool, step Step, cfg *EnvConfig) (*gatewayCallResult, error) {
	rawPayload, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("marshal payload: %w", err)
	}

	outerHeaders := map[string]string{
		"Domain":       "explorer",
		"Content-Type": "application/json",
		"X-Jwt-Token":  g.jwtToken,
	}

	// Build curl strings for logs (best-effort, never fatal). Values are kept
	// intact so generated logs can be replayed directly during debugging.
	gatewayCurl := constructCurl(endpoint, "POST", outerHeaders, string(rawPayload))
	businessCurl := buildBusinessCurl(payload, isHTTP, cfg)

	req, err := http.NewRequest(http.MethodPost, endpoint, bytes.NewReader(rawPayload))
	if err != nil {
		return nil, err
	}
	for k, v := range outerHeaders {
		req.Header.Set(k, v)
	}

	start := time.Now()
	resp, err := g.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("gateway request: %w", err)
	}
	defer resp.Body.Close()
	latencyMs := float64(time.Since(start).Microseconds()) / 1000.0

	respBytes, _ := io.ReadAll(resp.Body)
	gatewayLogID := resp.Header.Get("X-Tt-Logid")
	if gatewayLogID == "" {
		gatewayLogID = "N/A"
	}

	out := &gatewayCallResult{
		StatusCode:    resp.StatusCode,
		HasPermission: true,
		LatencyMs:     latencyMs,
		GatewayURL:    endpoint,
		GatewayLogID:  gatewayLogID,
		BusinessCurl:  businessCurl,
		GatewayCurl:   gatewayCurl,
		Timestamp:     time.Now().Format(time.RFC3339),
	}

	// Decode gateway envelope.
	var env gatewayResponse
	if jsonErr := json.Unmarshal(respBytes, &env); jsonErr == nil && resp.StatusCode == 200 {
		// Decode business `data` block.
		if len(env.Data) > 0 {
			var v any
			if err := decodeJSONUseNumber(env.Data, &v); err == nil {
				out.Body = normalizeNumbers(v)
			} else {
				out.Body = string(env.Data)
			}
		}
		out.Headers = env.RespHeaders
		out.LogIDDownstream = pickLogID(env.LogID, env.RespHeaders, resp.Header)
		out.BusinessCode = env.StatusCode
		out.GatewayErrorCode = env.ErrorCode
		if env.HasPerm != nil {
			out.HasPermission = *env.HasPerm
		}

		// Save full envelope for the runtime log block.
		var raw any
		_ = decodeJSONUseNumber(respBytes, &raw)
		out.GatewayBody = raw
	} else {
		// Non-200 / non-JSON gateway error: produce a fallback envelope so the
		// log writer and report parser still see something structured.
		var raw any
		if err := decodeJSONUseNumber(respBytes, &raw); err != nil {
			raw = map[string]any{
				"raw_text": string(respBytes),
			}
		}
		out.Body = raw
		out.GatewayBody = raw
		out.LogIDDownstream = "N/A"
	}
	return out, nil
}

func pickLogID(envelopeLogID string, respHeaders map[string]string, httpHeaders http.Header) string {
	if envelopeLogID != "" {
		return envelopeLogID
	}
	if respHeaders != nil {
		if v, ok := respHeaders["X-Tt-Logid"]; ok && v != "" {
			return v
		}
	}
	if v := httpHeaders.Get("X-Tt-Logid"); v != "" {
		return v
	}
	return "N/A"
}

// appendQuery appends params as a query string, preserving any existing one.
func appendQuery(path string, params map[string]string) string {
	if len(params) == 0 {
		return path
	}
	values := url.Values{}
	for k, v := range params {
		values.Add(k, v)
	}
	sep := "?"
	if strings.Contains(path, "?") {
		sep = "&"
	}
	return path + sep + values.Encode()
}

func buildBusinessCurl(payload gatewayRequest, isHTTP bool, cfg *EnvConfig) string {
	if !isHTTP {
		businessURL := fmt.Sprintf("rpc://%s/%s", payload.PSM, payload.FuncName)
		// Surface metainfo persistent values in the business curl as
		// "metainfo:<key>" headers so debugging readers can see what dyeing
		// tags were sent without having to re-decode the gateway envelope.
		headersForCurl := make(map[string]string, len(payload.Header)+len(payload.RpcContext))
		for k, v := range payload.Header {
			headersForCurl[k] = v
		}
		for _, item := range payload.RpcContext {
			headersForCurl["metainfo:"+item.Key] = item.Value
		}
		return constructCurl(businessURL, "POST", headersForCurl, payload.Request)
	}
	host := payload.Host
	psm := payload.PSM
	var businessURL string
	switch {
	case host != "":
		if !strings.HasPrefix(host, "http://") && !strings.HasPrefix(host, "https://") {
			businessURL = "https://" + host + payload.Path
		} else {
			businessURL = host + payload.Path
		}
	case psm != "":
		businessURL = "http://" + psm + payload.Path
	default:
		businessURL = payload.Path
	}
	body := payload.Request
	if strings.ToUpper(payload.Method) == "GET" {
		body = ""
	}
	return constructCurl(businessURL, payload.Method, payload.Header, body)
}

// constructCurl renders a copy-paste-ready curl invocation. The exact
// "--location --request" prefix is part of the contract with the report
// parser (it greps for that string), so don't change the layout lightly.
func constructCurl(targetURL, method string, headers map[string]string, body string) string {
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("curl --location --request %s '%s'", strings.ToUpper(method), targetURL))
	for k, v := range headers {
		sb.WriteString(fmt.Sprintf(" \\\n  --header '%s: %s'", k, v))
	}
	if body != "" {
		// single-quote-escape body
		escaped := strings.ReplaceAll(body, `'`, `'\''`)
		sb.WriteString(fmt.Sprintf(" \\\n  --data-raw '%s'", escaped))
	}
	return sb.String()
}
