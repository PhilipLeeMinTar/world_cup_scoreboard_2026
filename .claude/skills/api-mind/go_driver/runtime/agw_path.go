package apitest

import (
	"regexp"
	"strings"
)

var (
	agwTopLevelFields = map[string]struct{}{
		"code": {}, "data": {}, "message": {}, "logId": {}, "debugTraceInfo": {},
	}
	agwFirstFieldRE = regexp.MustCompile(`^\$\.((?:BaseResp\.)?[A-Za-z_][\w]*)`)
)

func isAGWEnvelope(root any) bool {
	m, ok := root.(map[string]any)
	if !ok {
		return false
	}
	_, hasCode := m["code"]
	_, hasData := m["data"]
	return hasCode && hasData
}

func agwAlternatePath(path string) (string, bool) {
	switch path {
	case "$.BaseResp.StatusCode":
		return "$.code", true
	case "$.BaseResp.StatusMessage":
		return "$.message", true
	}
	if strings.HasPrefix(path, "$.data.") || path == "$.code" || path == "$.message" {
		return "", false
	}
	m := agwFirstFieldRE.FindStringSubmatch(path)
	if m == nil {
		return "", false
	}
	field := strings.TrimPrefix(m[1], "BaseResp.")
	if field == "" {
		return "", false
	}
	if _, top := agwTopLevelFields[field]; top {
		if strings.HasPrefix(m[1], "BaseResp.") {
			return strings.Replace(path, "$.BaseResp.", "$.", 1), true
		}
		return "", false
	}
	return strings.Replace(path, m[0], "$.data."+field, 1), true
}

// jsonPathExtractWithMode resolves JSONPath against body. For HTTP mode, when the
// primary path misses on an AGW envelope ({code,data,message}), known IDL-style
// aliases are retried (e.g. $.BaseResp.StatusCode -> $.code, $.items -> $.data.items).
func jsonPathExtractWithMode(data any, path string, mode PathMode) (any, bool) {
	if v, ok := jsonPathExtractRaw(data, path); ok {
		return v, true
	}
	if mode != PathModeHTTP {
		return nil, false
	}
	root, ok := normalizeJSONInput(data)
	if !ok || !isAGWEnvelope(root) {
		return nil, false
	}
	alt, ok := agwAlternatePath(path)
	if !ok {
		return nil, false
	}
	return jsonPathExtractRaw(data, alt)
}

// jsonPathExtract keeps legacy call sites on RPC-style resolution (no AGW fallback).
func jsonPathExtract(data any, path string) (any, bool) {
	return jsonPathExtractWithMode(data, path, PathModeRPC)
}
