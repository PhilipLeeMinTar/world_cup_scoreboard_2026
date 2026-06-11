# EMO 常用命令

> 本文档总结了 EMO 的所有常用命令及其使用方法

## 安装 CLI

```bash
npm install -g @ies/eden-monorepo@latest
```

## 一、项目初始化

### emo init
初始化新的 Monorepo 项目

```bash
emo init  # 等价于 npx @byted/create@latest --emo
```

详细文档: https://edenx.bytedance.net/codesmith

### emo create
创建新的子项目

```bash
emo create                        # 创建子项目
emo create --dir libs             # 在 libs 目录下创建子项目
# 等价于 npx @byted/create@latest --emo-sub-prj
```

## 二、依赖管理

### emo install (别名: emo i)
安装项目依赖

```bash
# 对整个 monorepo 项目安装依赖
emo install

# 对部分子项目安装依赖
emo install --filter workspaceA --filter workspaceB

# 安装 infra 目录的依赖
emo install --infra

# CI 中冻结 lockfile
emo install --frozen-lockfile

# 只更新 lockfile,不安装
emo install --lockfile-only
```

**常用选项:**
- `--infra`: 安装 infra 目录或根目录下的依赖
- `--frozen-lockfile`: 不更改 lockfile,如果不同步则失败(CI 中默认开启)
- `--lockfile-only`: 只更新 pnpm-lock.yaml,不写入 node_modules
- `--fix-lockfile`: 自动修复损坏的 lockfile
- `--filter`: 筛选需要安装依赖的 workspace

### emo add
添加依赖

```bash
# 在子项目下运行
emo add react

# 在根目录下运行
emo add react --filter @byted-emo/edenx

# 添加为 devDependencies
emo add -D typescript

# 添加到指定版本
emo add react@18.0.0
```

### emo update
更新依赖

```bash
# 更新所有依赖
emo update

# 更新指定依赖
emo update react

# 更新到最新版本
emo update react --latest
```

### emo remove
移除依赖

```bash
# 移除依赖
emo remove react

# 从指定项目移除
emo remove react --filter @byted-emo/edenx
```

### emo reset
清空并重新安装

```bash
# 清空 node_modules 和 .eden-mono 并重新全量安装
emo reset
```

### emo clean
清除缓存和 node_modules

```bash
# 清除 .eden-mono 文件夹、infra 目录(或根目录)以及所有子项目中的 node_modules
emo clean
```

### emo run-pnpm
运行 pnpm 命令

```bash
# 查看依赖使用情况
emo run-pnpm why -r react
emo run-pnpm why -r react --filter "@byted-emo/edenx"

# 其他 pnpm 命令
emo run-pnpm <pnpm-command>
```

## 三、本地开发

### emo start
启动开发服务

```bash
# 在根目录下运行
emo start [workspace-name]

# 在子项目路径下运行
emo start
```

会自动预构建其在 workspace 内的所有依赖。

**脚本优先级配置 (eden.monorepo.json):**
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

### emo build
构建项目

```bash
# 在子项目下运行
emo build

# 在根目录运行(构建指定项目)
emo build [workspace-name]
```

### emo test
运行测试

```bash
# 在子项目下运行
emo test

# 在根目录运行(测试指定项目)
emo test [workspace-name]
```

### emo run
批量运行项目脚本

```bash
# 根目录运行,构建所有项目
emo run build

# 构建指定项目及其所有依赖
emo run build --filter "@byted-emo/edenx..."

# 构建指定目录下的所有项目
emo run build --filter './packages/'

# 构建除了某个项目之外的所有项目
emo run build --filter \!@byted-emo/edenx
```

### emo exec
在所有项目中执行命令

```bash
# 并行删除所有的 node_modules
emo exec 'rm -rf ./node_modules' -p

# 在指定项目中执行命令
emo exec 'ls' --filter @byted-emo/edenx
```

## 四、子项目管理

### emo register
注册子项目到配置文件

```bash
emo register <project-path>
```

### emo check
检查项目配置和规范

```bash
# 运行所有检查
emo check

# 运行特定检查
emo check --checker dependencyVersionCheck
```

## 五、版本发布

### emo add-changeset
添加变更集

```bash
emo add-changeset
```

交互式添加版本变更信息。

### emo version
更新版本号

```bash
# 根据 changeset 更新版本号和 CHANGELOG
emo version
```

### emo publish
发布包到 npm

```bash
# 发布所有需要更新的包
emo publish

# 发布 preview 版本
emo publish --tag preview

# 发布 prerelease 版本
emo publish --tag prerelease
```

## 六、CI/CD

### emo pipeline
运行 CI/CD 流水线

```bash
# Codebase CI 使用
emo pipeline --scene gitlab --trigger-branch create --target-branch $CI_EVENT_CHANGE_TARGET_BRANCH --revision origin/$CI_EVENT_CHANGE_TARGET_BRANCH
```

**配置文件 (eden.mono.pipeline.json):**
```json
{
  "$schema": "https://sf-unpkg-src.bytedance.net/@ies/eden-monorepo@3.6.1/lib/mono.pipeline.schema.json",
  "scene": {
    "codebase": {
      "buildAffected": true,
      "testAffected": true
    }
  }
}
```

### emo scm
触发 SCM 构建

```bash
# 根目录下使用
emo scm
```

**scm_build.sh 示例:**
```bash
#!/bin/bash
set -e

echo "node version is " && node -v

npm install -g @ies/eden-monorepo@3.6.1 --registry https://bnpm.byted.org

emo scm
```

**配置文件 (eden.mono.pipeline.json):**
```json
{
  "$schema": "https://sf-unpkg-src.bytedance.net/@ies/eden-monorepo@3.6.1/lib/mono.pipeline.schema.json",
  "scene": {
    "scm": {
      "emo/demo/edenx": {
        "entries": ["@byted-emo/edenx"]
      }
    }
  }
}
```

**子项目 build.sh 示例:**
```bash
#!/bin/bash
set -e

npm run deploy
```

## 七、其他命令

### emo config
配置 EMO

```bash
# 查看配置
emo config list

# 设置配置
emo config set <key> <value>
```

### emo recover
恢复项目状态

```bash
emo recover
```

### emo migrate
迁移项目到新版本

```bash
emo migrate
```

### emo plugin-install
安装插件依赖

```bash
# 安装所有插件的依赖
emo plugin-install --all-plugins

# 安装指定插件的依赖
emo plugin-install --plugin <plugin-name>
```

## 八、升级版本

### 升级 pnpm 版本

修改 `eden.monorepo.json`:
```json
{
  "$schema": "https://sf-unpkg-src.bytedance.net/@ies/eden-monorepo@3.6.1/lib/monorepo.schema.json",
  "config": {
    "infraDir": "infra",
-   "pnpmVersion": "7.32.0",
+   "pnpmVersion": "10.12.1",
    "edenMonoVersion": "3.6.1"
  }
}
```

### 升级 EMO 版本

修改 `eden.monorepo.json`:
```json
{
- "$schema": "https://sf-unpkg-src.bytedance.net/@ies/eden-monorepo@3.0.0/lib/monorepo.schema.json",
+ "$schema": "https://sf-unpkg-src.bytedance.net/@ies/eden-monorepo@3.6.1/lib/monorepo.schema.json",
  "config": {
    "infraDir": "infra",
    "pnpmVersion": "10.12.1",
-   "edenMonoVersion": "3.0.0",
+   "edenMonoVersion": "3.6.1"
  }
}
```

## 九、常用工作流

### 日常开发流程
```bash
# 1. 安装依赖
emo install

# 2. 启动开发(会自动预构建依赖)
cd apps/your-app
emo start

# 3. 构建
emo build

# 4. 测试
emo test
```

### 批量操作流程
```bash
# 1. 构建所有项目
emo run build

# 2. 测试所有项目
emo run test

# 3. 构建特定项目及其依赖
emo run build --filter "@byted-emo/edenx..."
```

### 发包流程
```bash
# 1. 添加变更集
emo add-changeset

# 2. 更新版本
emo version

# 3. 发布
emo publish
```

## 十、过滤器语法

EMO 使用 pnpm 的 filter 语法,支持以下模式:

```bash
# 按包名过滤
--filter "@byted-emo/edenx"

# 按路径过滤
--filter './packages/'

# 包含依赖
--filter "@byted-emo/edenx..."  # 包及其依赖
--filter "...@byted-emo/edenx"  # 包及其依赖者

# 排除包
--filter \!@byted-emo/edenx

# 组合使用
--filter '@byted-emo/edenx' --filter '@byted-emo/utils'
```

## 相关文档

- 官方 CLI 文档: https://emo.web.bytedance.net/cli/dep-management/install.html
- pnpm 过滤器文档: https://pnpm.io/filtering
