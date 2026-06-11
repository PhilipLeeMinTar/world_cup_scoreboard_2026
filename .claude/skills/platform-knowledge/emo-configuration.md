# EMO 配置指南

> 本文档详细介绍 EMO 的所有配置文件和配置项

## 配置文件概览

EMO 项目主要包含以下配置文件:

1. **eden.monorepo.json** - 主配置文件,配置整体功能和注册项目
2. **eden.mono.workspace.json** - 子项目配置文件
3. **eden.mono.pipeline.json** - CI/CD 流水线配置
4. **eden.mono.config.js** - 高级配置(JS)
5. **.npmrc** - npm 配置
6. **.pnpmfile.cjs** - pnpm hooks 配置

## 一、eden.monorepo.json (主配置)

### 基本结构

```json
{
  "$schema": "https://sf-unpkg-src.bytedance.net/@ies/eden-monorepo@3.6.1/lib/monorepo.schema.json",
  "config": {
    // 功能配置
  },
  "packages": [
    // 一对一注册子项目
  ],
  "workspaces": [
    // 或使用 glob 表达式注册
  ],
  "pnpmWorkspace": {
    // pnpm workspace 配置
  }
}
```

### config 配置项

#### 1. 版本管理

```json
{
  "config": {
    // 锁定 EMO 版本
    "edenMonoVersion": "3.6.1",

    // 锁定 pnpm 版本
    "pnpmVersion": "10.12.1"
  }
}
```

#### 2. 目录配置

```json
{
  "config": {
    // 基建目录
    "infraDir": "infra",

    // 插件目录
    "pluginsDir": "plugins"
  }
}
```

#### 3. 构建缓存配置

```json
{
  "config": {
    "cache": {
      // 缓存的输入(影响因素)
      "affectedInput": {
        // 环境变量
        "env": ["REGION", "GULU_ENV", "NODE_ENV"],

        // 文件('default' 或 string[])
        "file": "default",

        // 运行时命令
        "runtime": ["node -v"]
      },

      // 缓存的输出(需要缓存的目录)
      "storedOutput": ["build", "dist", "build_cn", "build_sg", "build_va", "build_gcp"],

      // 缓存策略: 'default' | 'isolated'
      "strategy": "default",

      // v3.2.0+ 为特定操作配置缓存
      "operations": {
        "build": {
          "affectedInput": {},
          "storedOutput": ["dist"],
          "strategy": "default"
        },
        "test": {
          "affectedInput": {},
          "storedOutput": [],
          "strategy": "isolated"
        }
      }
    }
  }
}
```

**缓存策略说明:**
- `default`: 本地可读写本地缓存+读取远端缓存,远端环境(CI/SCM)可读写远端缓存
- `isolated`: 本地可读写本地缓存,无远端缓存能力

**关闭缓存:**
```json
{
  "config": {
    "cache": false
  }
}
```

#### 4. Workspace 检查配置

```json
{
  "config": {
    "workspaceCheck": {
      // 检查外部依赖版本是否统一
      "dependencyVersionCheck": {
        "autofix": false,
        "forceCheck": false,
        "options": {
          "autofixMode": "newerVersion",  // 'newerVersion' | 'preferedVersions' | 'select'
          "excludes": [],                  // 不检查的依赖
          "includes": [],                  // 只检查的依赖
          "preferedVersions": {            // 指定依赖版本
            "react": "17.0.0"
          }
        }
      },

      // 检查 tag 关系
      "tagRelationCheck": {
        "autofix": false,
        "forceCheck": false,
        "options": {
          "admin-utils": ["admin"]  // admin-utils 只能被 admin 使用
        }
      },

      // 检查邮箱设置
      "emailCheck": {
        "forceCheck": true
      },

      // 外部依赖检查(幻影依赖等)
      "externalDependencyCheck": {
        "autofix": false,
        "forceCheck": false,
        "options": {
          // 安装了但未使用
          "installedButNotUsed": {
            "excludes": ["webpack"],
            "projectExcludes": {
              "@byted-emo/edenx": ["react"]
            }
          },
          // 使用了但未安装(幻影依赖)
          "usedButNotInstalled": {
            "excludes": ["webpack"],
            "projectExcludes": {
              "@byted-emo/edenx": ["react"]
            }
          }
        }
      },

      // 循环依赖检查
      "cycleDependencyCheck": {
        "autofix": false,
        "forceCheck": true,
        "options": {
          "projectGraphCycle": true
        }
      },

      // 项目依赖检查
      "projectDependencyCheck": false,

      // TypeScript project reference 检查
      "tsconfigProjectReferenceCheck": {
        "autofix": true,
        "forceCheck": true,
        "options": {
          // 忽略某个项目
          "excludes": ["<packageName>"],
          // 或忽略某个项目的某个依赖
          "excludes": {
            "<packageName>": ["<depPackageName>"]
          },
          // 设置 tsconfig 路径
          "projectTsconfigPath": {
            "<package_name>": "./tsconfig.custom.json"
          }
        }
      }
    }
  }
}
```

#### 5. 脚本名称配置

```json
{
  "config": {
    "scriptName": {
      "test": ["test"],
      "build": ["build"],
      "start": ["build:watch", "dev", "start", "serve"]
    }
  }
}
```

执行 `emo start/build/test` 时,会按照配置的优先级依次查找并执行对应的 npm script。

#### 6. 依赖图策略

```json
{
  "config": {
    // 'all' | 'semver'
    "pkgJsonDepsPolicies": "semver",

    // 是否从源码构建依赖图
    "buildProjectGraphFromSourceCode": false
  }
}
```

#### 7. 产物路径配置

```json
{
  "config": {
    "outputPaths": {
      "dirs": ["output", "output_resource"],
      "files": ["scm_build_resource.sh"]
    }
  }
}
```

SCM 构建时,会将这些目录和文件 copy 到顶层。

#### 8. 发包配置

```json
{
  "config": {
    "packagePublish": {
      // 发包工具
      "tool": "changesets",

      // 分析 cherry-pick 信息
      "analyzeCherryPickMsg": false,

      // 发包通知
      "notification": {
        // latest 版本通知
        "latest": {
          "toTriggerUser": true,
          "toUsers": ["xxx.xxx"],
          "toGroups": ["xxxxxxxxxxxxxx"]  // 飞书群组 ID
        },
        // preview 版本通知
        "preview": {},
        // prerelease 版本通知
        "prerelease": {}
      }
    }
  }
}
```

获取飞书群组 ID: https://open.feishu.cn/tool/token

#### 9. 插件配置

```json
{
  "config": {
    // 插件列表
    "plugins": [
      "@emo/plugin-example"
    ],

    // 插件目录
    "pluginsDir": "plugins",

    // 自动安装插件依赖
    "autoInstallDepsForPlugins": true
  }
}
```

#### 10. 模版生成器

```json
{
  "config": {
    "generator": [
      {
        "name": "react-component",
        "path": "./templates/react-component"
      }
    ]
  }
}
```

#### 11. 其他配置

```json
{
  "config": {
    // 手动维护 pnpm-workspace.yaml
    "manualPnpmWorkspace": false
  }
}
```

### packages 配置(一对一注册)

```json
{
  "packages": [
    {
      // 包名(可选)
      "name": "@byted-emo/edenx",

      // 路径(必填)
      "path": "apps/edenx",

      // 是否可发布(可选)
      "shouldPublish": true,

      // 源码入口(可选)
      "sourceEntryFile": "src",

      // 缓存配置(可选,覆盖全局配置)
      "cache": {
        // 同全局 cache 配置
      },

      // 标签(可选)
      "tags": ["admin", "utils"],

      // 隐式依赖(可选)
      "implicitDependencies": ["@emo/adam"]
    }
  ]
}
```

### workspaces 配置(glob 表达式)

```json
{
  "workspaces": [
    "apps/*",
    "packages/*",
    "libs/*"
  ]
}
```

**注意**: `packages` 和 `workspaces` 互斥,只能使用其中一个。

### pnpmWorkspace 配置

```json
{
  "pnpmWorkspace": {
    // workspace 包列表(优先级高于 workspaces)
    "packages": [
      "apps/*",
      "packages/*"
    ],

    // pnpm catalog(依赖版本目录)
    "catalog": {
      "react": "18.0.0",
      "react-dom": "18.0.0"
    },

    // pnpm catalogs(多个依赖版本目录)
    "catalogs": {
      "react17": {
        "react": "17.0.0",
        "react-dom": "17.0.0"
      },
      "react18": {
        "react": "18.0.0",
        "react-dom": "18.0.0"
      }
    }
  }
}
```

**在子项目中使用 catalog:**
```json
{
  "dependencies": {
    // 使用方式 1: 使用 catalog 中的默认版本
    "react": "catalog:default",
    "react-dom": "catalog:default",

    // 使用方式 2: 使用 catalogs 中特定版本
    "react": "catalog:react18",
    "react-dom": "catalog:react18"
  }
}
```

## 二、eden.mono.workspace.json (子项目配置)

放在子项目根目录,用于覆盖全局配置。

```json
{
  "$schema": "https://sf-unpkg-src.bytedance.net/@ies/eden-monorepo@3.6.1/lib/mono.workspace.schema.json",

  // 缓存配置(覆盖全局)
  "cache": {
    "affectedInput": {
      "env": ["NODE_ENV"]
    },
    "storedOutput": ["dist"]
  },

  // 标签
  "tags": ["admin"],

  // 隐式依赖
  "implicitDependencies": ["@emo/common"]
}
```

## 三、eden.mono.pipeline.json (CI/CD 配置)

### SCM 场景配置

```json
{
  "$schema": "https://sf-unpkg-src.bytedance.net/@ies/eden-monorepo@3.6.1/lib/mono.pipeline.schema.json",
  "scene": {
    "scm": {
      // SCM 项目名: 配置
      "emo/demo/edenx": {
        "entries": ["@byted-emo/edenx"]
      },
      "emo/demo/admin": {
        "entries": ["@byted-emo/admin"]
      }
    }
  }
}
```

### Codebase CI 场景配置

```json
{
  "$schema": "https://sf-unpkg-src.bytedance.net/@ies/eden-monorepo@3.6.1/lib/mono.pipeline.schema.json",
  "scene": {
    "codebase": {
      // 是否构建受影响的项目
      "buildAffected": true,

      // 是否测试受影响的项目
      "testAffected": true
    }
  }
}
```

## 四、.npmrc 配置

```ini
# npm registry
registry=https://bnpm.byted.org

# pnpm 配置
shamefully-hoist=false
strict-peer-dependencies=false

# 设置 node-linker
node-linker=hoisted
```

## 五、.pnpmfile.cjs 配置

用于 hook pnpm 的依赖安装流程。

```javascript
module.exports = {
  hooks: {
    // 读取 package 时触发
    readPackage(pkg, context) {
      // 修改依赖版本
      if (pkg.name === 'some-package') {
        pkg.dependencies = {
          ...pkg.dependencies,
          'some-dep': '^2.0.0'
        };
      }

      return pkg;
    }
  }
};
```

## 六、配置最佳实践

### 1. 推荐的基础配置

```json
{
  "$schema": "https://sf-unpkg-src.bytedance.net/@ies/eden-monorepo@3.6.1/lib/monorepo.schema.json",
  "config": {
    "edenMonoVersion": "3.6.1",
    "pnpmVersion": "10.12.1",
    "infraDir": "infra",
    "cache": {
      "strategy": "default"
    },
    "workspaceCheck": {
      "dependencyVersionCheck": true,
      "cycleDependencyCheck": {
        "forceCheck": true
      },
      "externalDependencyCheck": {
        "usedButNotInstalled": true
      }
    }
  },
  "workspaces": [
    "apps/*",
    "packages/*"
  ]
}
```

### 2. 大型项目配置建议

- 使用 `packages` 一对一注册,便于精细控制
- 开启依赖版本检查和自动修复
- 配置合理的缓存策略
- 使用 `catalog` 统一管理依赖版本
- 配置发包通知

### 3. 性能优化配置

```json
{
  "config": {
    "cache": {
      "strategy": "default",
      "operations": {
        "build": {
          "storedOutput": ["dist", "build"]
        }
      }
    },
    "buildProjectGraphFromSourceCode": false
  }
}
```

### 4. 严格模式配置

```json
{
  "config": {
    "workspaceCheck": {
      "dependencyVersionCheck": {
        "autofix": true,
        "forceCheck": true
      },
      "externalDependencyCheck": {
        "usedButNotInstalled": true,
        "installedButNotUsed": true
      },
      "cycleDependencyCheck": {
        "forceCheck": true
      }
    }
  }
}
```

## 相关文档

- 官方配置文档: https://emo.web.bytedance.net/config/eden-monorepo-json.html
- pnpm 配置: https://pnpm.io/npmrc
- Workspace 管理: https://emo.web.bytedance.net/tutorial/basic/workspace-management.html
