package apitest

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func writeEnvFile(t *testing.T, content string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), ".env")
	if err := os.WriteFile(path, []byte(strings.TrimSpace(content)+"\n"), 0o644); err != nil {
		t.Fatalf("write env fixture: %v", err)
	}
	return path
}

func TestLoadEnvLegacyFlatCreatesDefaultService(t *testing.T) {
	cfg, err := LoadEnv(writeEnvFile(t, `
psm: tiktok.demo.main
host: ppe-main.tiktok.com
env: ppe-main
branch: feature/main
zone: us-east-1
idc: va6
cluster: gray
`))
	if err != nil {
		t.Fatalf("LoadEnv: %v", err)
	}
	if err := cfg.Validate(); err != nil {
		t.Fatalf("Validate: %v", err)
	}
	if cfg.DefaultService != "default" {
		t.Fatalf("DefaultService = %q, want default", cfg.DefaultService)
	}
	if cfg.Services["default"].PSM != "tiktok.demo.main" {
		t.Fatalf("default service PSM = %q", cfg.Services["default"].PSM)
	}
	route, err := cfg.ResolveService("")
	if err != nil {
		t.Fatalf("ResolveService: %v", err)
	}
	if route.PSM != "tiktok.demo.main" || route.Env != "ppe-main" || route.Branch != "feature/main" || route.Host != "ppe-main.tiktok.com" {
		t.Fatalf("resolved route = %+v", route)
	}
}

func TestLoadEnvMultiServiceResolveBinding(t *testing.T) {
	cfg, err := LoadEnv(writeEnvFile(t, `
default_service: main

services:
  main:
    psm: tiktok.demo.main
    host: ppe-main.tiktok.com
    env: ppe-main
    branch: master
    zone: us-east-1
    idc: va6
    cluster: default

  user:
    psm: tiktok.demo.user
    host: ppe-user.tiktok.com
    env: ppe-user
    branch: feature/user
    zone: us-east-1
    idc: va6
    cluster: gray
`))
	if err != nil {
		t.Fatalf("LoadEnv: %v", err)
	}
	if err := cfg.Validate(); err != nil {
		t.Fatalf("Validate: %v", err)
	}
	if cfg.PSM != "tiktok.demo.main" || cfg.Env != "ppe-main" {
		t.Fatalf("default flat route = %+v", cfg)
	}
	route, err := cfg.ResolveService("user")
	if err != nil {
		t.Fatalf("ResolveService(user): %v", err)
	}
	if route.PSM != "tiktok.demo.user" || route.Host != "ppe-user.tiktok.com" || route.Env != "ppe-user" || route.Branch != "feature/user" || route.Cluster != "gray" {
		t.Fatalf("resolved user route = %+v", route)
	}
}

func TestLoadEnvMultiServiceRequiresDefaultService(t *testing.T) {
	cfg, err := LoadEnv(writeEnvFile(t, `
services:
  main:
    psm: tiktok.demo.main
  user:
    psm: tiktok.demo.user
`))
	if err != nil {
		t.Fatalf("LoadEnv: %v", err)
	}
	err = cfg.Validate()
	if err == nil || !strings.Contains(err.Error(), "default_service is required") {
		t.Fatalf("Validate error = %v, want default_service error", err)
	}
}

func TestLoadEnvRejectsUnknownDefaultService(t *testing.T) {
	cfg, err := LoadEnv(writeEnvFile(t, `
default_service: missing
services:
  main:
    psm: tiktok.demo.main
`))
	if err != nil {
		t.Fatalf("LoadEnv: %v", err)
	}
	err = cfg.Validate()
	if err == nil || !strings.Contains(err.Error(), `default_service "missing" not found`) {
		t.Fatalf("Validate error = %v, want unknown default_service error", err)
	}
}

func TestLoadEnvRequiresServicePSM(t *testing.T) {
	cfg, err := LoadEnv(writeEnvFile(t, `
services:
  main:
    env: ppe-main
`))
	if err != nil {
		t.Fatalf("LoadEnv: %v", err)
	}
	err = cfg.Validate()
	if err == nil || !strings.Contains(err.Error(), "services.main.psm is required") {
		t.Fatalf("Validate error = %v, want service psm error", err)
	}
}

func TestLoadEnvAppliesServiceDefaults(t *testing.T) {
	cfg, err := LoadEnv(writeEnvFile(t, `
services:
  main:
    psm: tiktok.demo.main
`))
	if err != nil {
		t.Fatalf("LoadEnv: %v", err)
	}
	if err := cfg.Validate(); err != nil {
		t.Fatalf("Validate: %v", err)
	}
	route, err := cfg.ResolveService("")
	if err != nil {
		t.Fatalf("ResolveService: %v", err)
	}
	if route.Env != "prod" || route.Branch != "master" || route.Cluster != "default" {
		t.Fatalf("defaults = env %q branch %q cluster %q", route.Env, route.Branch, route.Cluster)
	}
}
