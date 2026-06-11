# Overpass Troubleshooting Guide

## Important Notes

### What Overpass Oncall Can Help With

- Repository generation issues
- IDL parsing problems
- Code generation failures
- Platform configuration issues
- Template bugs

### What Overpass Oncall CANNOT Help With

**RPC Call Issues**: Overpass is a wrapper around Kitex framework. All RPC behavior depends on:
- **Framework**: Kitex
- **Environment**: BOE/PPE/Devbox/Mesh/TCE/Consul

**For RPC issues, contact**:
- Downstream service owner
- Kitex Oncall
- Environment-specific Oncall (PPE/BOE/Mesh/TCE/etc.)

## IDL Information Issues

### PSM Status Not OK

#### MainIDLFilePathNotSet

**Problem**: IDL path not configured in MS platform

**Solution**:
1. Configure IDL path following: https://bytedance.larkoffice.com/wiki/B1zmwRKqxiNfXzkGgIRcOL8Bndc
2. Click "Force Sync IDL Information" in Overpass web interface
3. Wait for sync to complete

#### MainIDLFileNotFound

**Problem**: IDL file path doesn't exist in repository

**Checks**:
1. Verify IDL path exists in the specified repository
2. Confirm service configured IDL path in MS (CN or I18n control plane)
3. Use unified IDL repository (recommended) instead of per-service repos

**Why unified IDL repos**: Decouples business code permissions from IDL access rights

#### IDLFileParseFailed

**Common Syntax Issues**:

1. **Full-width characters**: Must use half-width punctuation
   ```thrift
   // ❌ WRONG: Full-width comma
   struct Foo {
       1: string name,  // Full-width comma
   }

   // ✅ CORRECT
   struct Foo {
       1: string name,  // Half-width comma
   }
   ```

2. **Missing type prefix**: Must prefix types from other files
   ```thrift
   // common.thrift
   struct DataType { }

   // service.thrift
   include "common.thrift"

   // ❌ WRONG
   struct Req {
       1: DataType data
   }

   // ✅ CORRECT
   struct Req {
       1: common.DataType data
   }
   ```

3. **Missing field IDs in service methods**:
   ```thrift
   // ❌ WRONG
   service MyService {
       Response Hello(Request req)
   }

   // ✅ CORRECT
   service MyService {
       Response Hello(1: Request req)
   }
   ```

4. **Data IDL absolute path issues**: For IDL repos under `idl/*` namespace
   - Must use absolute paths (not relative)
   - Cannot mix `data/idl` style (absolute) with `service_rpc/idl` style (relative)
   - See: https://bytedance.larkoffice.com/wiki/wikcnxr9vbbUPr8eIGj3IqSPwxc

5. **Cross-repo reference permission issues**: If IDL references another repo, ensure Overpass has access

### PSM Not Found / Doesn't Exist

**Root Cause**: Overpass uses TCE API to discover PSMs. Services not on TCE aren't auto-discovered.

**Solution**: Use "Add to Whitelist" button in web interface

**Note**: Services must exist in production MS (not just BOE) for auto-discovery

### New Service Not in Overpass

**Requirements**:
1. Service created in TCE
2. IDL path configured in production MS (BOE config insufficient)

**Why production MS required**:
- Many services don't configure BOE MS IDL paths
- Production RPC calls must use production IDL

**Workaround**: Use "Add to Whitelist" if MS configuration pending

### IDL Updated But Repository Not Updated

**Update Timing**:
- IDL file change → 4 minutes detection
- MS IDL path update → 3 minutes detection
- Repository generation → 30 seconds

**Manual Force Update**:
1. "IDL Information Query" → "Force Sync IDL Information"
2. Verify "Last Update Time" shows latest timestamp
3. "Repository Information Management" → "Force Update Repository"

**Exponential Backoff**: After repeated failures, auto-update delays increase exponentially. Use force update to bypass.

## Repository Generation Issues

### CreateOrUpdateRepoFailed

#### Rate Limiting (429 Error)

**Error**: "The requested URL returned error: 429"

**Cause**: GitLab rate limiting during bulk operations (e.g., cold start)

**Solution**:
- Wait a few minutes
- Use "Force Update" for urgent needs
- Check "IDL Change Detection Time" to verify queue position

#### Remote Repo Not Created

**Error**: "remote repo not created yet, maybe Codebase or Kani delayed"

**Solution**:
1. Verify IDL file accessible via Overpass web interface
2. Confirm repository is empty
3. Contact Codebase Oncall to delete repository
4. Click "Force Update" to recreate

#### Undefined Type Error

**Error**: 'resolve field "xxx": undefined type: "xxx"'

**Cause**: Thrift syntax violation (often after recent commit)

**Solution**: Review changes against Thrift RFC: https://bytedance.larkoffice.com/wiki/RFC_Thrift_IDL

### GetServiceInfoFailed

**Checks**:
1. Verify IDL status is OK
2. Ensure service definition is not empty
3. For Webcast/TikCast: Check for business-specific restrictions
4. Contact Oncall if IDL parsing failure

### GenKitexFilesFailed

**Cause**: Kitex code generation failed (likely IDL syntax issue)

**Debugging**:
1. Verify IDL status is OK
2. Test locally with Kitex tool
3. Check for syntax errors
4. If confirmed Kitex bug, contact Kitex Oncall with Overpass Oncall

### GenOverpassFilesFailed

**Common Causes**:

1. **User code compilation failure** (Webcast: `init.go`, Others: `methods.go`)
   - Caused by incompatible IDL updates (deleted methods/types/fields)
   - Solution: Remove references to deleted IDL elements

2. **Service name changed** (Webcast specific)
   - Delete old files from `webcast/rpc_gen`
   - Delete `webcast/rpc_p_s_m/init.go`
   - Error message: "does not contain package code.byted.org/webcast/rpc_gen/kitex_gen/*"

3. **Missing service definition**
   - Error: "failed parsing source file rpc/XXX/overpass_client.go: no such file or directory"
   - Cause: Main IDL file has no `service` declaration
   - Solution: Add service definition to IDL

### Specific Error Patterns

#### Multiple Definition Error

**Error**: "multiple definition of 'XXX'" or "duplicated names in global scope"

**Cause**: Duplicate struct/enum/constant definitions in IDL

**Solution**: Remove duplicates, ensure unique naming

#### Common Repo Error

**Error**: "[runv2.updateCommonRepo] fail" + "search {repo}/xxx.thrift: file does not exist"

**Causes**:
1. Referenced file not configured as common structure
2. Related common structures in different repositories (must be same repo)

**Solution**: Update `.overpass/common.yml` configuration

#### Include Circle Error

**Error**: "found include circle"

**Example**:
```thrift
// a.thrift includes b.thrift
// b.thrift includes a.thrift  ❌
```

**Solution**: Remove circular dependencies. Thrift doesn't support circular includes.

#### Import Cycle Error

**Error**: "import cycle not allowed"

**Cause**: Similar to include circle, but at Go package level

**Solution**: Restructure IDL to eliminate cycles

#### Duplicate Field ID

**Error**: 'duplicated field ID 1 in struct "XXX"'

**Cause**: Multiple fields with same ID in struct

**Solution**: Ensure unique field IDs in each struct

#### Skip Code Review Failed

**Error**: 'skip code review failed, output={"message":"change not found"}'

**Cause**: Codebase API delay

**Solution**: Wait a few minutes or trigger "Force Update"

#### Base.thrift Multiple Copies

**Error**: "NewBaseResp redeclared" / "previous declaration at kitex_gen/base/base.go"

**Cause**: Multiple different `base.thrift` files with same namespace, causing conflicts

**Solution**: Use common structures feature (see Common Structures documentation)

## Repository Access Issues

### No Permission / Go Get Fails

**Error**: "Please make sure you have the correct access rights and the repository exists"

**Checks**:
1. Confirm repository status is "OK" in web interface
2. Verify you can access repository link
3. Check membership in "All R&D (Repository)" user group (key: `all_rd_repos`)
   - Contact 段文博 if not in group
4. For non-generic business lines, manually request repository access
5. Test GitLab connectivity with other repositories
6. If all checks pass, contact Codebase/Kani Oncall (possible auth delay)

### Repository Shows "Page Not Found"

**Issue**: Go import path ≠ GitLab web URL

**Explanation**:
```
Import path: code.byted.org/overpass/p_s_m/kitex_gen/base
Web URL:     https://code.byted.org/overpass/p_s_m/-/tree/master/kitex_gen/base
```

Don't use import path in browser. Use web interface links instead.

## Kitex/Thriftgo Version Issues

### Version Policy

Overpass uses **stable** Kitex/Thriftgo versions prioritizing compatibility over "latest".

**Update Trigger**: Only when critical bugs confirmed or significant stability improvements

**Check Version**: View in Overpass web interface or generated `go.mod`

**Request Upgrade**: If confirmed bug exists, contact Overpass Oncall with evidence

## IDE Issues

### GoLand Cannot Index / No Declaration Found

**Cause**: Generated files too large for GoLand's default limits

**Solutions**:

1. **Adjust GoLand file size limit** (recommended)
   - Settings → Editor → Code Style → Hard wrap at: increase value
   - Help → Edit Custom Properties → Add: `idea.max.intellisense.filesize=10000`

2. **Use VSCode** (with gopls)
   - Better handling of large generated files

3. **Contact downstream** about splitting services/IDL

**Note**: Kitex v1.3.3+ splits generated code into `k-${file}` files, significantly reducing this issue.

## Compilation Issues

### Not Enough Arguments Error

**Error**: "not enough arguments in call to iprot.ReadString" / "have () want (context.Context)"

**Cause**: Apache Thrift upgraded from v0.13.0 to v0.14.0 (breaking change)

**Solution**:
```bash
# Check current version
go list -m github.com/apache/thrift

# Downgrade to v0.13.0
go get github.com/apache/thrift@v0.13.0
```

**Prevention**: Never use `go get -u` for updates (upgrades transitive dependencies unpredictably)

### ReleaseReadBuffer Undefined

**Error**:
- "p.trans.stream.ReleaseReadBuffer undefined"
- "undefined: shmipc.Buffer"
- "t.stream.Malloc undefined"

**Cause**: `gopkg/thrift` depends on old `service_mesh/shmipc` version

**Solution**:
```bash
go get code.byted.org/gopkg/thrift@latest
```

**Note**: This is not an Overpass issue. Contact Kitex Oncall for gopkg/thrift problems.

### Package Conflict After Update

**Cause**: Overpass guarantees internal compilation. External conflicts are from:
1. Your dependency version conflicts
2. Base library incompatibilities

**Solution**:
- Resolve dependency conflicts in your project
- Contact relevant framework/component team about breaking changes

### Type Mismatch Between Repositories

**Problem**: Same IDL generates different types per repository

**Example**:
```go
// Both from same IDL but different types
import (
    base1 "code.byted.org/overpass/psm1/kitex_gen/base"
    base2 "code.byted.org/overpass/psm2/kitex_gen/base"
)

// Cannot assign: base1.Foo != base2.Foo
```

**Solution**: Use **Common Structures** feature (see dedicated documentation)

**Workaround**: Use https://github.com/jinzhu/copier for struct copying

## Call-Related Issues

### RPC Call Error

**Error**: "RPC Call PSM={X} method={Y} failed with error: {Z}"

**Important**: This is framework/downstream error, not Overpass issue

**Debug Steps**:
1. Check error details in {Z}
2. Verify downstream service health
3. Check network/mesh configuration
4. Contact downstream owner or Kitex Oncall

### RPCError with Status Code

**Format**: "RPCError{PSM:[...] Method:[...] ErrType:[...] OriginalErr:[...] BizStatusCode:[...] BizStatusMessage:[...]}"

**Type**: Wrapped error from Overpass (see Error Handling documentation)

**Not an Overpass bug**: Underlying error from downstream/framework

### Remote or Network Error

**Error**: "remote or network error: {}"

**Source**: Kitex framework or downstream service

**Solution**: Debug RPC call path, not Overpass configuration

### Required Field Not Set

**Error**: "Required field X is not set"

**Cause**: IDL incompatibility (downstream changed `required` fields)

**Solution**: Coordinate with downstream on IDL versioning

**Reference**: Kitex documentation on Requiredness in Go

### LogID Issues

**Problem**: No LogID / Incorrect LogID / Trace not linked

**Not Overpass Related**: Check:
1. Service mesh enabled
2. Context properly propagated through call chain
3. No code creating new context (breaks tracing)

### Missing Call Logs

**Checks**:

1. **Update Dependencies**:
   ```bash
   go get code.byted.org/overpass/...
   # or
   go get code.byted.org/kite/kitex@latest  # >= v1.2.7
   ```

2. **Verify Conf Not Disabled**: `opClient.Conf().EnableReqRespLog`

3. **Framework-Specific**:

   **Ginex** (>= v1.7.0):
   - Logs in: `rpc/{p.s.m}.client.span.log`
   - Reference: Ginex v1.7.0 breaking changes

   **Hertz** (>= v0.5.0):
   - Logs in: `rpc/{p.s.m}.call.log`

   **Kite** (>= v3.9.25):
   - May need: kitc >= v3.10.12, kitutil >= v3.8.1

   **Kitex** (>= v1.2.7):
   - Reference: Kitex v1.2.* release notes

## Environment Issues

### Request Not Routed to Correct Lane

**Not Overpass Related**: Check:
1. Context has correct env: `kitutil.NewCtxWithEnv(ctx, "ppe_xxx")`
2. Service depends on Mesh
3. Environment configuration
4. Contact platform/component Oncall

### Unexpected Log Output

**Issue**: req/resp logs without `WithReqRespLogsInfo`

**Explanation**: Auto-enabled in PPE/BOE for debugging (disabled for load tests)

**Filter in Search**:
```bash
# Exclude these logs
grep -v "pattern" log.file
```

**Control Behavior**:
```bash
# Force enable in devbox
export OVERPASS_OPTION_PRINT_REQ_RESP_LOG=1

# Force disable in PPE/BOE
export OVERPASS_OPTION_PRINT_REQ_RESP_LOG=0
```

## Branch Generation Issues

### Branch Not Exist

**Checks**:
1. Branch actually exists in repository
2. Correct IDL repository (check MS configuration)
3. For cross-repo IDL references, all repositories must have matching branch

### Generated Code Not Latest Locally

**Solutions**:
```bash
# Clear module cache
go clean -modcache

# Re-download specific version
go get code.byted.org/overpass/p_s_m@branch-name

# If still issues, contact Codebase Oncall
```

### TTP Sync Failed / SCM Compilation Failed

**Error**: "fatal: repository 'https://gitlab.codebase.tiktok-sote.org/overpass/.../.git/' not found"

**Solution**:
1. Request repository Developer access
2. Manually sync to TTP: See TTP Codebase Sync Flow guide
3. Ensure sync configuration includes required options
4. If unresolved, contact Codebase Oncall

**Sync Configuration**: Check screenshot boxes in TTP sync interface

## Advanced Issues

### Invalid Version Unknown Revision

**Cause**: Branch regeneration uses `push -f`, overwriting commits

**Scenario**: You go-get'd a commit SHA that no longer exists after regeneration

**Solution**:
```bash
# Remove old dependency
go mod edit -droprequire code.byted.org/overpass/p_s_m

# Or use replace temporarily
go mod edit -replace code.byted.org/overpass/p_s_m=...

# Re-download latest
go get code.byted.org/overpass/p_s_m@branch-name
```

### Combined Service Support

**Status**: Supported

**Activation**: Contact Overpass Oncall to configure Kitex parameters

### Option Type Invalid Panic

**Error**: "[Overpass Init] Client Option Type invalid at the position of X"

**Cause**: Wrong option type passed (Client Option vs Call Option)

**Debug**:
1. Check position X in options array
2. Verify Client Options at initialization
3. Verify Call Options at RPC call time
4. Check not passing request params as options

**Common Mistakes**:
- Client Option passed during RPC call
- Call Option passed during client creation
- Request parameter mistaken for option

**Local Debug**: Set breakpoint in `kitex-overpass-suite/kos/overpass_client_option_parser.go:84`

## Prevention Best Practices

1. **Never use `go get -u`**: Causes unpredictable transitive upgrades
2. **Pin critical dependencies**: Use `go.mod` replace if needed
3. **Test before merge**: Use branch generation for validation
4. **Monitor Overpass updates**: Check user group announcements
5. **Keep base dependencies current**: Especially Kitex/Thriftgo
6. **Use common structures**: Avoid type incompatibilities
7. **Enable CI checks**: Catch IDL issues before merge
8. **Document custom configs**: Especially for client creation

## Getting Help

### Before Contacting Oncall

1. **Check this guide**: Most issues documented here
2. **Verify basics**: IDL syntax, repository access, dependency versions
3. **Collect error details**: Full error messages, logs, reproduction steps
4. **Check status page**: Overpass platform status

### Contact Channels

- **Overpass Oncall**: Platform/generation issues
- **Kitex Oncall**: RPC framework issues
- **Downstream Owner**: Service-specific call issues
- **Codebase Oncall**: Repository/GitLab issues
- **Environment Oncall**: PPE/BOE/Mesh issues

### Information to Provide

1. PSM name and repository link
2. Full error message and logs
3. Steps to reproduce
4. Recent changes (IDL, code, config)
5. Environment (production/PPE/BOE/devbox)
6. Dependency versions (especially Kitex)
