// Package apitest auth.yaml support.
//
// auth.yaml stores business authentication headers (Cookie, Hex-Auth-Key,
// Authorization, Hex-Login-User-Info, ...) per named profile. Generated tests
// pull headers via ctx.AuthHeaders() / ctx.AuthHeadersFor(profile) instead of
// inlining literal values, so the same generated *_test.go works for everyone
// who pulls the repo without further configuration.
//
// Schema (see resources/env_template.md for reference):
//
//	version: 1
//	profiles:
//	  default:
//	    headers:
//	      Hex-Auth-Key: "..."
//	      Cookie: "..."
//	  admin:
//	    extends: default      # optional; resolved into a flat headers map
//	    headers:
//	      Hex-Auth-Key: "..."
//	case_profiles:
//	  TC-G02-01: admin
//
// LoadAuth flattens extends chains at load time and detects cycles. A missing
// auth.yaml is non-fatal — HeadersFor returns an empty map so APIs without
// auth still run. An undefined profile reference is fatal at call time.
package apitest

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// AuthConfig is the parsed, post-extends auth.yaml.
type AuthConfig struct {
	Version      int
	Profiles     map[string]map[string]string // profile name -> flat headers (extends already merged)
	CaseProfiles map[string]string            // case_id -> profile name
}

// LoadAuth parses an auth.yaml file. Returns (nil, nil) when the path does not
// exist so callers can treat "no auth file" as "no business auth needed".
func LoadAuth(path string) (*AuthConfig, error) {
	if path == "" {
		return nil, nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("read auth file %q: %w", path, err)
	}

	tree, err := parseAuthYAML(string(data))
	if err != nil {
		return nil, fmt.Errorf("parse auth file %q: %w", path, err)
	}

	cfg := &AuthConfig{
		Version:      0,
		Profiles:     map[string]map[string]string{},
		CaseProfiles: map[string]string{},
	}

	if v, ok := tree["version"].(string); ok {
		// version is parsed as string; tolerate both `version: 1` and `version: "1"`.
		var n int
		if _, scanErr := fmt.Sscanf(strings.TrimSpace(v), "%d", &n); scanErr == nil {
			cfg.Version = n
		}
	}

	rawProfiles, _ := tree["profiles"].(map[string]any)
	rawCaseProfiles, _ := tree["case_profiles"].(map[string]any)

	if err := flattenProfiles(rawProfiles, cfg); err != nil {
		return nil, fmt.Errorf("auth file %q: %w", path, err)
	}

	for caseID, v := range rawCaseProfiles {
		name, ok := v.(string)
		if !ok {
			return nil, fmt.Errorf("auth file %q: case_profiles[%s] must be a string profile name", path, caseID)
		}
		if _, exists := cfg.Profiles[name]; !exists {
			return nil, fmt.Errorf("auth file %q: case_profiles[%s] references undefined profile %q", path, caseID, name)
		}
		cfg.CaseProfiles[caseID] = name
	}

	return cfg, nil
}

// flattenProfiles resolves each profile's extends chain into a flat headers map.
func flattenProfiles(raw map[string]any, cfg *AuthConfig) error {
	if raw == nil {
		return nil
	}
	// Discover all profile names first so resolveProfile can reference siblings.
	for name, v := range raw {
		if _, ok := v.(map[string]any); !ok {
			return fmt.Errorf("profiles[%s] must be a map", name)
		}
	}
	for name := range raw {
		flat, err := resolveProfile(name, raw, map[string]bool{})
		if err != nil {
			return err
		}
		cfg.Profiles[name] = flat
	}
	return nil
}

// resolveProfile recursively merges extends chains. The base profile's headers
// are applied first; the current profile's headers override on collision.
func resolveProfile(name string, raw map[string]any, visiting map[string]bool) (map[string]string, error) {
	if visiting[name] {
		return nil, fmt.Errorf("profiles[%s]: extends cycle detected", name)
	}
	node, ok := raw[name].(map[string]any)
	if !ok {
		return nil, fmt.Errorf("profiles[%s]: undefined profile in extends chain", name)
	}
	visiting[name] = true
	defer func() { delete(visiting, name) }()

	result := map[string]string{}

	if base, ok := node["extends"].(string); ok && base != "" {
		baseFlat, err := resolveProfile(base, raw, visiting)
		if err != nil {
			return nil, err
		}
		for k, v := range baseFlat {
			result[k] = v
		}
	}

	headers, _ := node["headers"].(map[string]any)
	for k, v := range headers {
		s, ok := v.(string)
		if !ok {
			return nil, fmt.Errorf("profiles[%s].headers[%s]: must be a string", name, k)
		}
		result[k] = s
	}
	return result, nil
}

// HeadersFor returns a copy of the headers selected by, in order:
//  1. an explicit profile name (when non-empty)
//  2. the case_profiles[caseID] mapping
//  3. the "default" profile
//
// An empty map is returned when no usable profile is found, so endpoints
// without business auth (and tests that intentionally skip auth) still work.
// An explicit-but-undefined profile name is a hard fatal — generated code
// is the only place where profile names appear, and a typo there must surface.
func (a *AuthConfig) HeadersFor(caseID, profile string) (map[string]string, error) {
	if a == nil {
		return map[string]string{}, nil
	}
	if profile != "" {
		h, ok := a.Profiles[profile]
		if !ok {
			return nil, fmt.Errorf("auth: profile %q not defined in auth.yaml", profile)
		}
		return cloneHeaders(h), nil
	}
	if name, ok := a.CaseProfiles[caseID]; ok {
		return cloneHeaders(a.Profiles[name]), nil
	}
	if h, ok := a.Profiles["default"]; ok {
		return cloneHeaders(h), nil
	}
	return map[string]string{}, nil
}

func cloneHeaders(in map[string]string) map[string]string {
	out := make(map[string]string, len(in))
	for k, v := range in {
		out[k] = v
	}
	return out
}

// ── minimal YAML subset parser ────────────────────────────────────────────
//
// Supports just enough for auth.yaml:
//   - top-level scalar:  `key: value`
//   - nested map:        `key:` followed by an indented block
//   - leaf scalar:       string, optionally single/double quoted
//   - comments / blanks: `# ...` / empty lines
//
// No flow style, no anchors, no list (`- `). Indentation must use spaces and
// be consistent at each level. Tabs are rejected.
type authNode struct {
	indent   int
	tree     map[string]any
	parent   *authNode
	parentKey string
}

func parseAuthYAML(content string) (map[string]any, error) {
	root := map[string]any{}
	stack := []*authNode{{indent: -1, tree: root}}
	scanner := bufio.NewScanner(strings.NewReader(content))
	scanner.Buffer(make([]byte, 64*1024), 1024*1024)

	lineNo := 0
	for scanner.Scan() {
		lineNo++
		raw := scanner.Text()
		if strings.ContainsRune(raw, '\t') {
			return nil, fmt.Errorf("line %d: tabs are not allowed in auth.yaml; use spaces", lineNo)
		}
		trimmed := strings.TrimSpace(raw)
		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			continue
		}
		// Strip trailing inline comment that is NOT inside quotes.
		trimmed = stripInlineComment(trimmed)
		if trimmed == "" {
			continue
		}

		indent := countLeadingSpaces(raw)
		// Pop stack frames until we find a parent with strictly smaller indent.
		for len(stack) > 1 && stack[len(stack)-1].indent >= indent {
			stack = stack[:len(stack)-1]
		}
		parent := stack[len(stack)-1]

		key, value, isSection, err := parseAuthLine(trimmed)
		if err != nil {
			return nil, fmt.Errorf("line %d: %v", lineNo, err)
		}
		if isSection {
			child := map[string]any{}
			parent.tree[key] = child
			stack = append(stack, &authNode{
				indent:    indent,
				tree:      child,
				parent:    parent,
				parentKey: key,
			})
			continue
		}
		parent.tree[key] = value
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return root, nil
}

func parseAuthLine(line string) (key, value string, isSection bool, err error) {
	idx := strings.IndexByte(line, ':')
	if idx < 0 {
		return "", "", false, fmt.Errorf("expected `key: value` or `key:`")
	}
	key = strings.TrimSpace(line[:idx])
	if key == "" {
		return "", "", false, fmt.Errorf("empty key")
	}
	rest := strings.TrimSpace(line[idx+1:])
	if rest == "" {
		return key, "", true, nil
	}
	return key, unquote(rest), false, nil
}

func unquote(v string) string {
	if len(v) >= 2 {
		if (v[0] == '"' && v[len(v)-1] == '"') || (v[0] == '\'' && v[len(v)-1] == '\'') {
			return v[1 : len(v)-1]
		}
	}
	return v
}

func countLeadingSpaces(line string) int {
	n := 0
	for _, ch := range line {
		if ch != ' ' {
			break
		}
		n++
	}
	return n
}

// stripInlineComment removes ` # ...` (with at least one space before #) when
// the # is not inside single/double quotes. Conservative — only strips when
// the # is preceded by whitespace, so tokens like `Bearer #abc` survive.
func stripInlineComment(line string) string {
	inSingle, inDouble := false, false
	for i := 0; i < len(line); i++ {
		ch := line[i]
		switch ch {
		case '\'':
			if !inDouble {
				inSingle = !inSingle
			}
		case '"':
			if !inSingle {
				inDouble = !inDouble
			}
		case '#':
			if !inSingle && !inDouble && i > 0 && line[i-1] == ' ' {
				return strings.TrimSpace(line[:i])
			}
		}
	}
	return line
}
