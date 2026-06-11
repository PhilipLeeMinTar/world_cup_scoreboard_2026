# Overpass Common Structures

## The Problem

When multiple PSMs reference the same IDL file, Overpass generates separate copies in each repository. This creates a type incompatibility issue:

```go
import (
    "code.byted.org/overpass/p_s_m1/kitex_gen/psm1"
    "code.byted.org/overpass/p_s_m2/kitex_gen/psm2"
)

func main() {
    var req1 psm1.Request1
    var req2 psm2.Request2

    // COMPILATION ERROR: Cannot assign!
    // Even though both use the same base.thrift
    req1.Base = req2.Base
}
```

**Root Cause**: Go treats packages from different paths as different types:
- `code.byted.org/overpass/p_s_m1/kitex_gen/base`
- `code.byted.org/overpass/p_s_m2/kitex_gen/base`

## The Solution: Common Structure Repositories

Overpass generates shared IDL structures into a **common repository** that multiple PSM repositories can depend on.

### Architecture

```
Common Repo (e.g., cpputil/model)
    ↓ (dependency)
PSM1 Repo (overpass/p_s_m1)
PSM2 Repo (overpass/p_s_m2)
PSM3 Repo (overpass/p_s_m3)
```

All PSMs now share the same `base.Base` type from the common repository.

## Benefits

1. **Type Compatibility**: Same IDL = same Go type across all PSMs
2. **Code Deduplication**: Common structures generated once, not per PSM
3. **Proven Reliability**: 20+ IDL repos, 480+ PSMs successfully using this approach

## Setup Process

### First-Time Setup (Manual)

If `.overpass/common.yml` doesn't exist in your IDL repository:

#### Step 1: Create Common Repository

1. Create a new repository (e.g., `overpass/{team}_{idl_repo}_common`)
2. Grant **@范峥** at least Developer access
3. Ensure repository has a default branch (usually `master`)
4. If no default branch exists, grant **@范峥** Master access

#### Step 2: Configure CI Check (Optional but Recommended)

Add validation to prevent invalid IDL merges:

1. Create `.codebase/pipelines/CheckCommonIDL.yaml`
2. Create `.codebase/pipelines/checkCommonIDL.sh`
3. Copy content from: https://code.byted.org/tiktok-tns-eng/idl/merge_requests/1450

**Purpose**: Validates common structure configuration before merge

#### Step 3: Configure Common Structures

Create `.overpass/common.yml` in your IDL repository root:

```yaml
# Format: IDL_FILE_PATH: COMMON_REPO_NAME

# Example 1: Single common structure
base.thrift: cpputil/model

# Example 2: Multiple structures in same repo
ecom/model/extension/extension.thrift: ecom/model
ecom/model/business/xiaodian.recycle_business.thrift: ecom/model

# Example 3: Nested structure with dependencies
base.thrift: myteam/common
types.thrift: myteam/common  # Referenced by base.thrift
utils.thrift: myteam/common  # Referenced by types.thrift
```

**Requirements**:
- Each IDL path must be absolute (relative to IDL repo root)
- Each IDL file must have `namespace go` configured
- Within same common repo, namespace conflicts not allowed
- If IDL A references IDL B, both must be in same common repo

#### Step 4: Generate Code

**Option A: Branch Generation**
1. Go to "IDL Information Query" page
2. Click "Branch Generation"
3. Enter branch name and click "Get Branch IDL"
4. Click "Generate Repository"
5. Pull the branch code

**Option B: Master Generation**
1. In "IDL Information Query", click "Force Sync IDL Information"
2. Wait for sync (check "Last Update Time")
3. In "Repository Information Management", click "Trigger Update Repository"
4. Wait for code generation (~30 seconds)

#### Step 5: Verify Results

**Check Common Repository**:
```
code.byted.org/{common_repo_name}/
├── go.mod
├── go.sum
├── kitex_gen/
│   └── base/          # Your common structures
│       ├── base.go
│       └── ...
```

**Check PSM Repository**:
```
code.byted.org/overpass/p_s_m/
├── go.mod               # Should contain common repo dependency
│   # require code.byted.org/{common_repo_name} vX.X.X
├── kitex_gen/
│   └── psm/            # PSM-specific structures only
```

**Verify go.mod**:
```bash
# Common repo should be in dependencies
grep "code.byted.org/{common_repo_name}" go.mod
```

### Adding New Common Structures

Edit `.overpass/common.yml` to add more common structures:

```yaml
# Existing
base.thrift: cpputil/model

# Add new common structures
common/types.thrift: cpputil/model
common/errors.thrift: cpputil/model
```

Then trigger regeneration (see Step 4 above).

## Configuration Rules

### File Path Requirements

```yaml
# ✅ CORRECT: Absolute path from IDL repo root
base.thrift: cpputil/model
common/types.thrift: cpputil/model

# ❌ WRONG: Relative path
./base.thrift: cpputil/model
../common/types.thrift: cpputil/model
```

### Repository Assignment

```yaml
# ✅ CORRECT: Related structures in same repo
base.thrift: myteam/common
types.thrift: myteam/common
utils.thrift: myteam/common

# ❌ WRONG: Dependent structures in different repos
base.thrift: myteam/common
types.thrift: myteam/types  # But base.thrift references types.thrift!
```

### Namespace Requirements

Each common IDL file must declare Go namespace:

```thrift
// ✅ CORRECT
namespace go base

struct Base {
    1: string LogID
}

// ❌ WRONG: Missing namespace
struct Base {
    1: string LogID
}
```

### Avoiding Conflicts

Within same common repository, no namespace conflicts allowed:

```yaml
# ❌ WRONG: Both use "namespace go common"
common/v1/types.thrift: myteam/common  # namespace go common
common/v2/types.thrift: myteam/common  # namespace go common

# ✅ CORRECT: Different namespaces
common/v1/types.thrift: myteam/common  # namespace go common.v1
common/v2/types.thrift: myteam/common  # namespace go common.v2

# ✅ ALSO CORRECT: Separate repositories
common/v1/types.thrift: myteam/common_v1  # namespace go common
common/v2/types.thrift: myteam/common_v2  # namespace go common
```

## White-list Policy

**Status**: Fully released, no white-list restrictions

Previous white-list mechanism has been removed. Any IDL repository with `.overpass/common.yml` automatically enables common structures for all associated PSMs.

If you need custom white-list configuration (e.g., only enable for specific PSMs), contact Overpass Oncall.

## CI Validation

### Purpose

Prevents invalid IDL from breaking Overpass code generation:
- Validates `.overpass/common.yml` syntax
- Checks for namespace conflicts
- Verifies dependency relationships
- Ensures all referenced files exist

### Setup

Copy from reference MR: https://code.byted.org/tiktok-tns-eng/idl/merge_requests/1450

**Files needed**:
```
.codebase/pipelines/
├── CheckCommonIDL.yaml
└── checkCommonIDL.sh
```

### What it Checks

1. **File Existence**: All IDL files in `common.yml` must exist
2. **Namespace Validity**: Each file has valid `namespace go` declaration
3. **No Conflicts**: No duplicate namespaces in same common repo
4. **Dependency Closure**: Referenced IDLs are also in common structures
5. **Repository Mapping**: 1:N relationship (1 IDL repo → N common repos)

## Troubleshooting

### Issue: Code Not Updated After Configuration

**Solutions**:
1. Force sync IDL information (web interface)
2. Force update repository (web interface)
3. Check "Last Update Time" to verify sync
4. Wait for exponential backoff to complete (if previous failures)

### Issue: Common Repo Not Created

**Check**:
1. Repository exists and is accessible
2. @范峥 has appropriate permissions
3. Default branch exists in repository
4. No typos in `common.yml`

### Issue: Compilation Errors After Enabling

**Possible Causes**:
```go
// Type mismatch if mixing old and new dependencies
import (
    "code.byted.org/overpass/p_s_m/kitex_gen/base"  // Old
    "code.byted.org/cpputil/model/kitex_gen/base"    // New
)
```

**Solution**: Clean module cache and re-download:
```bash
go clean -modcache
go mod tidy
go get code.byted.org/overpass/...
```

### Issue: Namespace Conflict Error

**Error**: "namespace conflict in common repository"

**Solution**: Use different namespaces or separate repos:
```thrift
// Option 1: Different namespaces
namespace go base.v1  // file1.thrift
namespace go base.v2  // file2.thrift

// Option 2: Separate repos
file1.thrift: team/common_v1
file2.thrift: team/common_v2
```

### Issue: CI Check Fails

**Common Reasons**:
1. Missing `namespace go` in IDL
2. Circular dependencies
3. Referenced IDL not in `common.yml`
4. File path typos

**Solution**: Follow CI error message and fix IDL

## Migration Guide

### From PSM-Local to Common Structures

1. **Identify Common IDLs**: Find IDL files shared across multiple PSMs
2. **Create Common Repo**: Set up dedicated repository
3. **Configure `common.yml`**: Map IDL files to common repo
4. **Trigger Generation**: Force update all affected PSMs
5. **Update Imports**: Change PSM-local imports to common repo imports
6. **Test Compilation**: Verify all services compile
7. **Deploy**: Roll out changes

### Handling Dependencies

If PSM repositories have circular dependencies:

```yaml
# All interdependent structures must be in same common repo
base.thrift: team/common
types.thrift: team/common      # Referenced by base.thrift
constants.thrift: team/common  # References types.thrift
```

## Best Practices

1. **Group Related Structures**: Keep logically related IDLs in same common repo
2. **Use Semantic Versioning**: Consider common repo versioning strategy
3. **Enable CI Checks**: Always configure validation pipeline
4. **Document Mappings**: Comment your `common.yml` for clarity
5. **Plan Namespace Hierarchy**: Design namespaces to avoid conflicts
6. **Test Before Merge**: Use branch generation to validate changes
7. **Coordinate Updates**: Communicate common structure changes across teams

## Example Configuration

### Example 1: Simple Base Structure

```yaml
# .overpass/common.yml
base.thrift: company/base_common
```

### Example 2: Domain Model

```yaml
# .overpass/common.yml
# E-commerce domain models
ecom/model/product.thrift: company/ecom_common
ecom/model/order.thrift: company/ecom_common
ecom/model/payment.thrift: company/ecom_common
```

### Example 3: Layered Architecture

```yaml
# .overpass/common.yml
# Data layer
common/data/base.thrift: company/data_common
common/data/types.thrift: company/data_common

# Business layer (separate repo for clear separation)
common/business/models.thrift: company/business_common
common/business/errors.thrift: company/business_common
```

## Limitations

1. **One IDL Repo → Multiple Common Repos**: Supported
2. **Multiple IDL Repos → One Common Repo**: Not supported
3. **Partial PSM Enablement**: Requires manual white-list (contact Oncall)
4. **Cross-Repo Dependencies**: Not supported (all deps must be in config)

## FAQ

**Q: Do I need to modify business code after enabling common structures?**
A: No. The change is transparent to your business logic. Only import paths change internally.

**Q: Can I add more common structures after initial setup?**
A: Yes. Just update `common.yml` and trigger regeneration.

**Q: What if automatic configuration only lists 10 structures?**
A: You can manually add more structures to `common.yml`.

**Q: Can different teams use the same common repository?**
A: Technically yes, but coordinate namespace usage to avoid conflicts.

**Q: How do I handle IDL versioning?**
A: Use namespace versioning (e.g., `namespace go base.v1`) or separate repos per version.

## References

- [RFC] Kitex_gen Common Structure Solution
- Kitex: Common Structure Reference Generation
- Overpass Web Interface: https://overpass.arcosite.bytedance.com
