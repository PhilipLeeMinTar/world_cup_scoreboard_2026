package apitest

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// LoadEnv parses the fixed apitest .env format without external YAML modules.
// Supported syntax is intentionally small: top-level `key: value`, optional
// leading `- ` for legacy single-item lists, and a fixed nested `services:` map
// for multi-PSM routing. A legacy indented `test_account:` map can still be
// parsed for backward compatibility, but generated `.env` files must not store
// sensitive authentication material.
func LoadEnv(path string) (*EnvConfig, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("read env file %q: %w", path, err)
	}
	defer file.Close()

	cfg := &EnvConfig{Services: map[string]ServiceConfig{}, TestAccount: map[string]string{}}
	section := ""
	currentService := ""
	scanner := bufio.NewScanner(file)
	lineNo := 0
	for scanner.Scan() {
		lineNo++
		rawLine := scanner.Text()
		trimmed := strings.TrimSpace(rawLine)
		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			continue
		}
		if strings.HasPrefix(trimmed, "- ") {
			trimmed = strings.TrimSpace(strings.TrimPrefix(trimmed, "- "))
		}
		key, value, ok := splitEnvLine(trimmed)
		if !ok {
			return nil, fmt.Errorf("parse env file %q line %d: expected key: value", path, lineNo)
		}
		indent := countIndent(rawLine)
		if indent == 0 && key == "services" {
			section = "services"
			currentService = ""
			if cfg.Services == nil {
				cfg.Services = map[string]ServiceConfig{}
			}
			continue
		}
		if indent == 0 && key == "test_account" {
			section = "test_account"
			currentService = ""
			if cfg.TestAccount == nil {
				cfg.TestAccount = map[string]string{}
			}
			continue
		}
		if section == "services" && isIndented(rawLine) {
			if value == "" && indent <= 2 {
				currentService = key
				if strings.TrimSpace(currentService) == "" {
					return nil, fmt.Errorf("parse env file %q line %d: services entry name is empty", path, lineNo)
				}
				if cfg.Services == nil {
					cfg.Services = map[string]ServiceConfig{}
				}
				if _, ok := cfg.Services[currentService]; !ok {
					cfg.Services[currentService] = ServiceConfig{}
				}
				continue
			}
			if currentService == "" {
				return nil, fmt.Errorf("parse env file %q line %d: service field %q without service name", path, lineNo, key)
			}
			svc := cfg.Services[currentService]
			if !assignServiceField(&svc, key, cleanEnvValue(value)) {
				return nil, fmt.Errorf("parse env file %q line %d: unsupported service field %q", path, lineNo, key)
			}
			cfg.Services[currentService] = svc
			continue
		}
		if section == "test_account" && isIndented(rawLine) {
			cfg.TestAccount[key] = cleanEnvValue(value)
			continue
		}
		section = ""
		currentService = ""
		assignEnvField(cfg, key, cleanEnvValue(value))
	}
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("read env file %q: %w", path, err)
	}
	applyEnvDefaults(cfg)
	return cfg, nil
}

func splitEnvLine(line string) (string, string, bool) {
	idx := strings.IndexByte(line, ':')
	if idx < 0 {
		return "", "", false
	}
	key := strings.TrimSpace(line[:idx])
	value := strings.TrimSpace(line[idx+1:])
	if key == "" {
		return "", "", false
	}
	return key, value, true
}

func isIndented(line string) bool {
	return strings.HasPrefix(line, " ") || strings.HasPrefix(line, "\t")
}

func countIndent(line string) int {
	count := 0
	for _, r := range line {
		switch r {
		case ' ':
			count++
		case '\t':
			count += 2
		default:
			return count
		}
	}
	return count
}

func cleanEnvValue(value string) string {
	value = strings.TrimSpace(value)
	if value == "{}" {
		return ""
	}
	if len(value) >= 2 && ((value[0] == '"' && value[len(value)-1] == '"') || (value[0] == '\'' && value[len(value)-1] == '\'')) {
		return value[1 : len(value)-1]
	}
	return value
}

func assignEnvField(cfg *EnvConfig, key, value string) {
	switch key {
	case "psm":
		cfg.PSM = value
	case "host":
		cfg.Host = value
	case "env":
		cfg.Env = value
	case "branch":
		cfg.Branch = value
	case "zone":
		cfg.Zone = value
	case "idc":
		cfg.IDC = value
	case "cluster":
		cfg.Cluster = value
	case "default_service":
		cfg.DefaultService = value
	}
}

func assignServiceField(svc *ServiceConfig, key, value string) bool {
	switch key {
	case "psm":
		svc.PSM = value
	case "host":
		svc.Host = value
	case "env":
		svc.Env = value
	case "branch":
		svc.Branch = value
	case "zone":
		svc.Zone = value
	case "idc":
		svc.IDC = value
	case "cluster":
		svc.Cluster = value
	default:
		return false
	}
	return true
}

func applyEnvDefaults(c *EnvConfig) {
	if c == nil {
		return
	}
	if c.Services == nil {
		c.Services = map[string]ServiceConfig{}
	}
	if len(c.Services) == 0 && c.PSM != "" {
		c.Services["default"] = serviceFromFlat(c)
		if c.DefaultService == "" {
			c.DefaultService = "default"
		}
	}
	for name, svc := range c.Services {
		applyServiceDefaults(&svc)
		c.Services[name] = svc
	}
	if c.DefaultService == "" && len(c.Services) == 1 {
		for name := range c.Services {
			c.DefaultService = name
		}
	}
	if c.DefaultService != "" {
		if svc, ok := c.Services[c.DefaultService]; ok {
			copyServiceToFlat(c, svc)
		}
	}
	if len(c.Services) == 0 {
		applyFlatDefaults(c)
	}
}

func serviceFromFlat(c *EnvConfig) ServiceConfig {
	return ServiceConfig{
		PSM:     c.PSM,
		Host:    c.Host,
		Env:     c.Env,
		Branch:  c.Branch,
		Zone:    c.Zone,
		IDC:     c.IDC,
		Cluster: c.Cluster,
	}
}

func applyServiceDefaults(svc *ServiceConfig) {
	if svc.Env == "" {
		svc.Env = "prod"
	}
	if svc.Cluster == "" {
		svc.Cluster = "default"
	}
	if svc.Branch == "" {
		svc.Branch = "master"
	}
}

func applyFlatDefaults(c *EnvConfig) {
	if c.Env == "" {
		c.Env = "prod"
	}
	if c.Cluster == "" {
		c.Cluster = "default"
	}
	if c.Branch == "" {
		c.Branch = "master"
	}
}

func copyServiceToFlat(c *EnvConfig, svc ServiceConfig) {
	c.PSM = svc.PSM
	c.Host = svc.Host
	c.Env = svc.Env
	c.Branch = svc.Branch
	c.Zone = svc.Zone
	c.IDC = svc.IDC
	c.Cluster = svc.Cluster
}

// ResolveService returns a single-service routing view. Empty service selects
// DefaultService. The returned EnvConfig keeps Services/TestAccount for helper
// compatibility but exposes the selected service through legacy flat fields.
func (c *EnvConfig) ResolveService(service string) (*EnvConfig, error) {
	if c == nil {
		return nil, fmt.Errorf("env config is nil")
	}
	applyEnvDefaults(c)
	if service == "" {
		service = c.DefaultService
	}
	if len(c.Services) > 0 {
		if service == "" {
			return nil, fmt.Errorf("env config: default_service is required")
		}
		svc, ok := c.Services[service]
		if !ok {
			return nil, fmt.Errorf("env config: service %q not found", service)
		}
		applyServiceDefaults(&svc)
		out := *c
		out.DefaultService = service
		copyServiceToFlat(&out, svc)
		return &out, nil
	}
	out := *c
	applyFlatDefaults(&out)
	return &out, nil
}

// Validate enforces the minimal field set required by the gateway client.
func (c *EnvConfig) Validate() error {
	if c == nil {
		return fmt.Errorf("env config is nil")
	}
	applyEnvDefaults(c)
	if len(c.Services) == 0 {
		if c.PSM == "" {
			return fmt.Errorf("env config: psm is required")
		}
		return nil
	}
	if len(c.Services) > 1 && c.DefaultService == "" {
		return fmt.Errorf("env config: default_service is required when multiple services are configured")
	}
	if c.DefaultService != "" {
		if _, ok := c.Services[c.DefaultService]; !ok {
			return fmt.Errorf("env config: default_service %q not found in services", c.DefaultService)
		}
	}
	for name, svc := range c.Services {
		if strings.TrimSpace(name) == "" {
			return fmt.Errorf("env config: service name is empty")
		}
		if svc.PSM == "" {
			return fmt.Errorf("env config: services.%s.psm is required", name)
		}
	}
	if c.PSM == "" {
		return fmt.Errorf("env config: psm is required")
	}
	return nil
}
