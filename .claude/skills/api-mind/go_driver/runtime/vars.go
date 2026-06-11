package apitest

import (
	"fmt"
	"regexp"
	"strings"
)

// context holds the three-tier variable scope used during a Case run:
//
//	extracted (set by Step.Extract on prior steps) > case > global
//
// Lookup precedence is highest-first.
type context struct {
	global    map[string]any
	caseVars  map[string]any
	extracted map[string]any
}

func newContext(global, caseVars map[string]any) *context {
	return &context{
		global:    cloneVarMap(global),
		caseVars:  cloneVarMap(caseVars),
		extracted: make(map[string]any),
	}
}

func cloneVarMap(in map[string]any) map[string]any {
	out := make(map[string]any, len(in))
	for k, v := range in {
		out[k] = v
	}
	return out
}

func (c *context) get(name string) (any, bool) {
	if v, ok := c.extracted[name]; ok {
		return v, true
	}
	if v, ok := c.caseVars[name]; ok {
		return v, true
	}
	if v, ok := c.global[name]; ok {
		return v, true
	}
	return nil, false
}

func (c *context) setExtracted(name string, value any) {
	c.extracted[name] = value
}

// variablePattern matches both placeholder syntaxes: try the double-brace
// form first, fall back to the single-brace form. The single-brace branch
// deliberately excludes nested `{` / `}` so it can never eat half of `${{ x }}`.
var variablePattern = regexp.MustCompile(`\$\{\{(.+?)\}\}|\$\{([^{}\n]+?)\}`)

// resolveValue walks any JSON-like value (map / slice / string / scalar) and
// substitutes every placeholder it finds. Strings that consist of exactly one
// placeholder return the raw resolved value, preserving int/list/map typing.
// Other strings are produced via fmt.Sprint per-placeholder.
func resolveValue(v any, c *context) any {
	switch val := v.(type) {
	case nil:
		return nil
	case string:
		return resolveString(val, c)
	case map[string]any:
		out := make(map[string]any, len(val))
		for k, sub := range val {
			out[k] = resolveValue(sub, c)
		}
		return out
	case map[string]string:
		out := make(map[string]string, len(val))
		for k, sub := range val {
			r := resolveString(sub, c)
			out[k] = fmt.Sprint(r)
		}
		return out
	case []any:
		out := make([]any, len(val))
		for i, sub := range val {
			out[i] = resolveValue(sub, c)
		}
		return out
	case []string:
		out := make([]any, len(val))
		for i, sub := range val {
			out[i] = resolveValue(sub, c)
		}
		return out
	default:
		return v
	}
}

func resolveString(s string, c *context) any {
	matches := variablePattern.FindAllStringSubmatchIndex(s, -1)
	if len(matches) == 0 {
		return s
	}

	// Single-placeholder fast path: keep raw type (int / map / list / ...).
	if len(matches) == 1 {
		m := matches[0]
		if m[0] == 0 && m[1] == len(s) {
			return resolvePlaceholder(captureExpr(s, m), c)
		}
	}

	// Multi-placeholder or partial: stringify each substitution.
	var sb strings.Builder
	cursor := 0
	for _, m := range matches {
		sb.WriteString(s[cursor:m[0]])
		expr := captureExpr(s, m)
		val := resolvePlaceholder(expr, c)
		if val != nil {
			sb.WriteString(fmt.Sprint(val))
		}
		cursor = m[1]
	}
	sb.WriteString(s[cursor:])
	return sb.String()
}

// captureExpr returns the inner expression for whichever alternative matched.
// match indexes follow regexp.FindAllStringSubmatchIndex semantics:
//
//	[0]=full start, [1]=full end,
//	[2..3]=double-brace inner, [4..5]=single-brace inner.
func captureExpr(s string, m []int) string {
	if m[2] != -1 {
		return strings.TrimSpace(s[m[2]:m[3]])
	}
	return strings.TrimSpace(s[m[4]:m[5]])
}

// resolvePlaceholder returns the variable value if it exists, otherwise the
// raw double-brace form is returned so the unresolved placeholder shows up
// verbatim in logs.
func resolvePlaceholder(expr string, c *context) any {
	if v, ok := c.get(expr); ok {
		return v
	}
	return "${{" + expr + "}}"
}
