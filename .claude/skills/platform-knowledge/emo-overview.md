# EMO (Eden Monorepo) 知识库

> **EMO V3** - 字节跳动 Monorepo 解决方案完整文档

## 📚 文档目录

### [01. EMO 介绍](./01-introduction.md)
- 什么是 EMO
- 核心特性与优势
- 主要功能概览
- 快速上手指南

### [02. 常用命令](./02-commands.md)
- 项目初始化命令
- 依赖管理命令
- 本地开发命令
- 构建与测试命令
- CI/CD 命令
- 版本发布命令
- 完整命令速查表

### [03. 配置指南](./03-configuration.md)
- eden.monorepo.json 主配置
- eden.mono.workspace.json 子项目配置
- eden.mono.pipeline.json CI/CD 配置
- 缓存配置详解
- Workspace 检查配置
- 完整配置示例

### [04. 最佳实践与进阶功能](./04-best-practices.md)
- 避免幻影依赖
- 统一依赖版本
- 基于源码开发
- 构建缓存优化
- 插件系统使用
- 自动化发包配置
- 常见问题解决

## 🚀 快速开始

### 安装 EMO CLI

```bash
npm install -g @ies/eden-monorepo@latest
```

### 创建新项目

```bash
# 初始化 Monorepo 项目
emo init

# 添加子项目
emo create

# 安装依赖
emo install

# 启动开发
emo start
```

## 📖 常用命令速查

### 依赖管理
```bash
emo install                    # 安装依赖
emo add <package>             # 添加依赖
emo remove <package>          # 移除依赖
emo reset                     # 重置并重新安装
```

### 开发构建
```bash
emo start [workspace]         # 启动开发
emo build [workspace]         # 构建项目
emo test [workspace]          # 运行测试
emo run build                 # 批量构建
```

### 版本发布
```bash
emo add-changeset            # 添加变更集
emo version                  # 更新版本号
emo publish                  # 发布包
```

## 🔧 核心特性

### ⚡ 性能优化
- **极速依赖安装**: 基于 pnpm 的高效依赖管理
- **增量构建**: 只构建变更的项目
- **构建缓存**: 本地和远程缓存支持
- **并行执行**: 自动并发构建和测试

### 🛡️ 工程治理
- **幻影依赖检测**: 自动检测并修复幻影依赖问题
- **版本统一管理**: 确保所有项目使用统一的依赖版本
- **循环依赖检查**: 防止项目间循环依赖
- **TypeScript 支持**: 完整的 TS 项目引用检查

### 🔄 CI/CD 集成
- **Codebase CI**: 深度集成公司 CI 系统
- **SCM 构建**: 一键触发 SCM 发布
- **增量构建**: 只构建受影响的项目
- **自动发包**: 基于 Changeset 的自动化发布

### 🎨 开发体验
- **自动链接**: 本地项目自动链接,无需 npm link
- **源码开发**: 支持基于源码的依赖开发
- **模版生成器**: 自定义项目模版
- **插件系统**: 灵活的插件扩展能力

## 📁 项目结构示例

```
my-monorepo/
├── apps/                      # 应用项目
│   ├── web-app/
│   └── mobile-app/
├── packages/                  # 共享包
│   ├── ui-components/
│   ├── utils/
│   └── api-client/
├── docs/                      # 文档
├── .eden-mono/               # EMO 缓存
├── eden.monorepo.json        # 主配置文件
├── eden.mono.pipeline.json   # CI/CD 配置
├── package.json
├── pnpm-lock.yaml
└── pnpm-workspace.yaml
```

## ⚙️ 基础配置示例

### eden.monorepo.json

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

## 🔗 相关资源

### 官方资源
- **官方文档**: https://emo.web.bytedance.net/
- **代码仓库**: https://code.byted.org/web-solutions/emo
- **更新日志**: https://emo.web.bytedance.net/changelog/3-9-release.html
- **用户群**: [飞书群组](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=e21je7dc-d791-4920-9d37-2e702675810d)

### 技术栈
- **pnpm**: https://pnpm.io/
- **Changesets**: https://github.com/changesets/changesets
- **Codebase**: 公司内部 CI 系统
- **SCM**: 公司内部发布系统

## 💡 使用建议

### 适合场景
✅ 多个相关项目需要统一管理
✅ 需要在多个项目间共享代码
✅ 希望统一工程规范和工具链
✅ 需要高效的构建和发布流程
✅ 项目规模较大,需要专业治理

### 不适合场景
❌ 单一独立项目
❌ 项目间完全独立无共享
❌ 不需要统一管理的多仓库

## 🆘 常见问题

### Q: 如何升级 EMO 版本?
修改 `eden.monorepo.json` 中的 `edenMonoVersion` 和 `$schema` 字段,然后运行 `emo install`。

### Q: 如何处理幻影依赖?
运行 `emo check --checker externalDependencyCheck --autofix`。

### Q: 如何统一依赖版本?
使用 `dependencyVersionCheck` 或 pnpm `catalog` 功能。

### Q: 构建缓存不生效?
检查 `cache` 配置,确保 `affectedInput` 和 `storedOutput` 配置正确。

### Q: CI 构建失败?
检查 `eden.mono.pipeline.json` 配置,确保 `build.sh` 脚本正确。

更多问题请查看: https://emo.web.bytedance.net/faq/project-init.html

## 📝 更新日志

- **v3.9.0** - 最新版本,查看完整更新: https://emo.web.bytedance.net/changelog/3-9-release.html
- **v3.6.1** - 稳定版本
- **v3.2.0** - 增加 operations 缓存配置
- **v3.0.0** - EMO V3 正式版

## 🤝 贡献与反馈

如果在使用 EMO 过程中遇到问题或有建议,欢迎:
- 加入用户群交流
- 提交 Issue
- 查阅官方文档

---

**维护者**: Web Infra - Web Solutions Team
**版本**: EMO V3
**最后更新**: 2025-11-25
