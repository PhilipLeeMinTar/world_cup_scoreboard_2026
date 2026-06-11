// Package apitest fixture helpers — dynamic test data builders for *_test.go.
//
// These helpers exist so generated tests stay deterministic across replays:
//   - UniqueName ensures CreateXxx calls don't collide on uniqueness constraints.
//   - Now*/Past*/Future* produce timestamps in the unit the field expects.
//   - RandString/RandInt/PickOne supply low-stakes filler data.
//   - Sample looks up an env-specific business value declared in the test
//     package's `envSamples` map.
//
// Hardcoding name / description / timestamp literals defeats the purpose; use
// these helpers instead. Routing env belongs in <specDir>/.env (loaded via
// NewContextFromSpec); business auth headers belong in <specDir>/auth.yaml
// profiles and are pulled in via ctx.AuthHeaders() / ctx.AuthHeadersFor(...).
package apitest

import (
	"fmt"
	"math/rand"
	"strings"
	"testing"
	"time"
)

// UniqueName returns "<prefix>_<unix_seconds>_<4-char random>".
// Use it for any field carrying a uniqueness constraint (entity Name, Code, ...).
func UniqueName(prefix string) string {
	return fmt.Sprintf("%s_%d_%s", prefix, time.Now().Unix(), randSuffix(4))
}

// NowSec returns the current Unix time in seconds.
func NowSec() int64 { return time.Now().Unix() }

// NowMilli returns the current Unix time in milliseconds.
func NowMilli() int64 { return time.Now().UnixMilli() }

// NowMicro returns the current Unix time in microseconds.
func NowMicro() int64 { return time.Now().UnixMicro() }

// PastSec returns Unix seconds at (now - d).
func PastSec(d time.Duration) int64 { return time.Now().Add(-d).Unix() }

// PastMilli returns Unix milliseconds at (now - d).
func PastMilli(d time.Duration) int64 { return time.Now().Add(-d).UnixMilli() }

// PastMicro returns Unix microseconds at (now - d).
func PastMicro(d time.Duration) int64 { return time.Now().Add(-d).UnixMicro() }

// FutureSec returns Unix seconds at (now + d).
func FutureSec(d time.Duration) int64 { return time.Now().Add(d).Unix() }

// RandString returns n random characters from the lowercase alphanumeric set.
// Suitable for description filler, suffix, etc. Not cryptographic.
func RandString(n int) string { return randSuffix(n) }

// RandInt returns a random int in [min, max). Caller guarantees min < max.
func RandInt(min, max int) int { return min + rand.Intn(max-min) }

// PickOne returns a random element from choices. choices must be non-empty.
func PickOne[T any](choices []T) T { return choices[rand.Intn(len(choices))] }

// Sample looks up an environment-specific business value from the calling
// package's envSamples table. The convention is:
//
//	var envSamples = map[string]map[string]string{
//	    "boei18n": {"PINNED_OWNER": "..."},
//	    "prod":    {"PINNED_OWNER": "..."},
//	}
//
// Sample(t, env, "PINNED_OWNER", envSamples) returns the value for the current
// env.Env, or t.Skip when the slot is unconfigured. Missing fixtures fail
// visibly instead of polluting the run with bogus data. envSamples is passed
// explicitly so apitest stays decoupled from any per-package symbol.
func Sample(t *testing.T, env *EnvConfig, key string, samples map[string]map[string]string) string {
	t.Helper()
	if v, ok := samples[env.Env][key]; ok && v != "" {
		return v
	}
	t.Skipf("apitest: sample %q not configured for env %q; add it to envSamples in this file", key, env.Env)
	return ""
}

func randSuffix(n int) string {
	const letters = "abcdefghijklmnopqrstuvwxyz0123456789"
	var sb strings.Builder
	sb.Grow(n)
	for i := 0; i < n; i++ {
		sb.WriteByte(letters[rand.Intn(len(letters))])
	}
	return sb.String()
}
