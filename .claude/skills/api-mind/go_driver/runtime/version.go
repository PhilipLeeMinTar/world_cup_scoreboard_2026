package apitest

// Version is the semantic version of this apitest runtime.
//
// Treat it as a stability contract:
//   - patch (X.Y.Z+1)  bug-fix only; no public symbol added/removed/renamed; no signature change.
//   - minor (X.Y+1.0)  new public symbols allowed; existing ones must keep behavior.
//   - major (X+1.0.0)  breaking change; old symbols may be removed/renamed.
//
// The api-mind skill ships a vendored copy
// of this runtime under go_driver/runtime/ along with a manifest.json. On every
// run the skill compares this constant against manifest.version and runs a
// compile-verify-then-rollback dance before overwriting any local file.
// See go_driver/apitest.md §5 for the full maintenance protocol.
const Version = "2.3.2"

// SourceCommit is informational only: the upstream commit this baseline was
// imported from. Not used for any runtime decision.
const SourceCommit = "5ef88f26147e9bd345167602ee44100af20175d1"
