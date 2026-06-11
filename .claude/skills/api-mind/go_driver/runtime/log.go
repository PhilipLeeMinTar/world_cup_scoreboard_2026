package apitest

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// writeCaseLog writes one StepResult into the case-level log file. The first
// step for a case truncates any stale file from an earlier go test run; later
// steps in the same case append so multi-step scenarios keep their full trace.
func writeCaseLog(logDir, caseID string, step Step, call *gatewayCallResult, appendLog bool) error {
	if logDir == "" {
		return nil
	}
	if err := os.MkdirAll(logDir, 0o755); err != nil {
		return err
	}
	path := filepath.Join(logDir, fmt.Sprintf("apitest_%s.log", caseID))
	flag := os.O_CREATE | os.O_WRONLY | os.O_TRUNC
	if appendLog {
		flag = os.O_CREATE | os.O_WRONLY | os.O_APPEND
	}
	f, err := os.OpenFile(path, flag, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()

	_, err = f.WriteString(formatLogEntry(step, call))
	return err
}

func formatLogEntry(step Step, call *gatewayCallResult) string {
	var sb strings.Builder

	if step.Name != "" {
		sb.WriteString(fmt.Sprintf("===== Step: %s =====\n", step.Name))
	}
	sb.WriteString(fmt.Sprintf("--- Request: Business (Curl) ---\n%s\n\n", call.BusinessCurl))

	bodyStr := pretty(call.Body)
	if strings.TrimSpace(bodyStr) == "" {
		bodyStr = "N/A"
	}
	sb.WriteString(fmt.Sprintf("--- Response: Business (JSON) ---\n%s\n\n", bodyStr))

	if len(call.Headers) > 0 {
		hStr := pretty(call.Headers)
		sb.WriteString(fmt.Sprintf("--- Response: Business Headers (JSON) ---\n%s\n\n", hStr))
	}

	businessStatus := "N/A"
	if call.BusinessCode != 0 {
		businessStatus = fmt.Sprintf("%d", call.BusinessCode)
	}
	sb.WriteString("--- Metadata: Business ---\n")
	sb.WriteString(fmt.Sprintf("Business.StatusCode: %s\n", businessStatus))
	sb.WriteString(fmt.Sprintf("Business.LogID: %s\n\n", call.LogIDDownstream))

	sb.WriteString("--- Metadata: Gateway ---\n")
	sb.WriteString(fmt.Sprintf("Gateway.Timestamp: %s\n", call.Timestamp))
	sb.WriteString(fmt.Sprintf("Gateway.HTTPStatusCode: %d\n", call.StatusCode))
	sb.WriteString(fmt.Sprintf("Gateway.LatencyMs: %.3f\n", call.LatencyMs))
	sb.WriteString(fmt.Sprintf("Gateway.HasPermission: %v\n", call.HasPermission))
	sb.WriteString(fmt.Sprintf("Gateway.ErrorCode: %d\n", call.GatewayErrorCode))
	sb.WriteString(fmt.Sprintf("Gateway.LogID: %s\n", call.GatewayLogID))

	sb.WriteString(fmt.Sprintf("\n\n--- Runtime: Gateway Request (Curl) ---\n%s", call.GatewayCurl))
	if call.GatewayBody != nil {
		gb := pretty(call.GatewayBody)
		sb.WriteString(fmt.Sprintf("\n\n--- Runtime: Gateway Response ---\n%s", gb))
	}
	sb.WriteString("\n\n")
	return sb.String()
}

func pretty(v any) string {
	switch t := v.(type) {
	case nil:
		return "N/A"
	case string:
		return t
	}
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return fmt.Sprint(v)
	}
	return string(b)
}
