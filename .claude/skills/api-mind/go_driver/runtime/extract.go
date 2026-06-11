package apitest

// extractAll evaluates every JSONPath in `cfg` against `body` and returns the
// resulting variable map. Missing paths produce a nil entry.
func extractAll(body any, cfg map[string]string, mode PathMode) map[string]any {
	out := make(map[string]any, len(cfg))
	for name, path := range cfg {
		if val, ok := jsonPathExtractWithMode(body, path, mode); ok {
			out[name] = val
		} else {
			out[name] = nil
		}
	}
	return out
}
