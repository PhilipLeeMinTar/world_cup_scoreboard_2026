package apitest

// injectHeaders merges optional legacy env-level headers with step headers;
// step headers win on collision. Newly generated tests should place business
// auth directly in step headers, not in `.env` test_account. RPC steps skip env
// header injection entirely (HTTP only).
func injectHeaders(stepType string, stepHeaders, envHeaders map[string]string) map[string]string {
	out := make(map[string]string, len(stepHeaders)+len(envHeaders))
	if stepType == "RPC" {
		for k, v := range stepHeaders {
			out[k] = v
		}
		return out
	}
	for k, v := range envHeaders {
		out[k] = v
	}
	for k, v := range stepHeaders {
		out[k] = v
	}
	return out
}
