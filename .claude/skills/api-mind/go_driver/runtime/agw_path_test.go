package apitest

import (
	"strings"
	"testing"
)

func agwBody() map[string]any {
	return map[string]any{
		"code":    float64(0),
		"message": "success",
		"data": map[string]any{
			"scenarios": []any{map[string]any{"id": "s1"}},
			"total":     float64(75),
		},
	}
}

func TestAGWAlternatePath(t *testing.T) {
	tests := []struct {
		in   string
		want string
		ok   bool
	}{
		{"$.BaseResp.StatusCode", "$.code", true},
		{"$.BaseResp.StatusMessage", "$.message", true},
		{"$.items", "$.data.items", true},
		{"$.total", "$.data.total", true},
		{"$.scenarios[0].id", "$.data.scenarios[0].id", true},
		{"$.code", "", false},
		{"$.data.items", "", false},
	}
	for _, tc := range tests {
		got, ok := agwAlternatePath(tc.in)
		if ok != tc.ok || got != tc.want {
			t.Errorf("agwAlternatePath(%q) = (%q, %v), want (%q, %v)", tc.in, got, ok, tc.want, tc.ok)
		}
	}
}

func assertNumEqual(t *testing.T, label string, got any, want float64) {
	t.Helper()
	f, ok := asFloat(got)
	if !ok || f != want {
		t.Fatalf("%s: got %v (%T), want %v", label, got, got, want)
	}
}

func TestJSONPathExtractWithModeHTTPFallback(t *testing.T) {
	body := agwBody()

	if v, ok := jsonPathExtractWithMode(body, "$.BaseResp.StatusCode", PathModeHTTP); !ok {
		t.Fatal("BaseResp.StatusCode fallback: path miss")
	} else {
		assertNumEqual(t, "BaseResp.StatusCode", v, 0)
	}
	if v, ok := jsonPathExtractWithMode(body, "$.items", PathModeHTTP); ok {
		t.Fatalf("$.items should miss without fallback alias (field is scenarios): %v", v)
	}
	if v, ok := jsonPathExtractWithMode(body, "$.total", PathModeHTTP); !ok {
		t.Fatal("$.total fallback: path miss")
	} else {
		assertNumEqual(t, "$.total", v, 75)
	}
	if v, ok := jsonPathExtractWithMode(body, "$.data.total", PathModeHTTP); !ok {
		t.Fatal("$.data.total direct: path miss")
	} else {
		assertNumEqual(t, "$.data.total", v, 75)
	}
}

func TestJSONPathExtractWithModeRPCNoFallback(t *testing.T) {
	body := agwBody()
	if _, ok := jsonPathExtractWithMode(body, "$.BaseResp.StatusCode", PathModeRPC); ok {
		t.Fatal("RPC mode must not apply AGW fallback")
	}
}

func TestIsAGWEnvelope(t *testing.T) {
	if !isAGWEnvelope(agwBody()) {
		t.Fatal("expected AGW envelope")
	}
	if isAGWEnvelope(map[string]any{"code": 0}) {
		t.Fatal("missing data should not match")
	}
}

func TestConstructCurlPreservesSensitiveAuthParameters(t *testing.T) {
	curl := constructCurl("https://paas-gw.example/api", "POST", map[string]string{
		"X-Jwt-Token":   "jwt-for-replay",
		"Authorization": "Bearer auth-secret",
		"Cookie":        "sessionid=cookie-secret",
	}, `{"access_token":"secret"}`)

	for _, want := range []string{
		"X-Jwt-Token: jwt-for-replay",
		"Authorization: Bearer auth-secret",
		"Cookie: sessionid=cookie-secret",
		`{"access_token":"secret"}`,
	} {
		if !strings.Contains(curl, want) {
			t.Fatalf("sensitive parameter should be preserved in log curl; missing %q, got: %s", want, curl)
		}
	}
	if strings.Contains(curl, "<redacted>") {
		t.Fatalf("log curl should not redact any sensitive parameter, got: %s", curl)
	}
}
