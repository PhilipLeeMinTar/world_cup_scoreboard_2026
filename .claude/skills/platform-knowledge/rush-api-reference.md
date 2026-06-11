# Rush.js API 参考手册

## Rush SDK 概述

Rush SDK 提供了丰富的 API 用于自动化脚本和插件开发，基于 `@microsoft/rush-lib` 包。这些 API 可以帮助开发者构建自定义工具、自动化脚本和插件。

### 核心模块
- **RushConfiguration** - 配置管理
- **RushSession** - 会话管理
- **PackageJsonEditor** - 包管理
- **ProjectManager** - 项目管理

## 配置管理 API

### RushConfiguration

#### 加载配置
```typescript
import { RushConfiguration } from '@microsoft/rush-lib';

// 从默认位置加载配置
const rushConfiguration = RushConfiguration.loadFromDefaultLocation({
  startingFolder: process.cwd()
});

// 从指定位置加载配置
const rushConfiguration = RushConfiguration.loadFromDefaultLocation({
  startingFolder: '/path/to/monorepo'
});
```

#### 获取项目信息
```typescript
// 获取所有项目
const projects = rushConfiguration.projects;
console.log(`Total projects: ${projects.length}`);

// 遍历项目
for (const project of projects) {
  console.log(`Project: ${project.packageName}`);
  console.log(`Folder: ${project.projectRelativeFolder}`);
  console.log(`Should publish: ${project.shouldPublish}`);
}

// 查找特定项目
const project = rushConfiguration.findProjectByShorthandName('my-app');
if (project) {
  console.log(`Found project: ${project.packageName}`);
}
```

#### 获取配置信息
```typescript
// 获取 Rush 版本
console.log(`Rush version: ${rushConfiguration.rushVersion}`);

// 获取 pnpm 版本
console.log(`pnpm version: ${rushConfiguration.pnpmVersion}`);

// 获取支持的 Node.js 版本
console.log(`Node version range: ${rushConfiguration.nodeSupportedVersionRange}`);

// 获取项目根目录
console.log(`Rush folder: ${rushConfiguration.rushFolder}`);
```

### 项目配置管理

#### 项目属性
```typescript
interface RushProject {
  packageName: string;                    // 包名
  projectRelativeFolder: string;          // 项目相对路径
  shouldPublish: boolean;                // 是否应该发布
  reviewCategory: string;                // 审查类别
  versionPolicyName?: string;            // 版本策略名称
  decoupledLocalDependencies: string[];  // 解耦的本地依赖
  cyclicDependencyProjects: string[];     // 循环依赖项目
}
```

#### 项目依赖管理
```typescript
// 获取项目依赖
const project = rushConfiguration.findProjectByShorthandName('my-app');
if (project) {
  // 获取依赖项目
  const dependencies = project.dependencyProjects;
  console.log('Dependencies:', dependencies.map(p => p.packageName));
  
  // 获取消费项目
  const consumers = project.consumingProjects;
  console.log('Consumers:', consumers.map(p => p.packageName));
}
```

## 包管理 API

### PackageJsonEditor

#### 创建编辑器
```typescript
import { RushConfiguration } from '@microsoft/rush-lib';

const rushConfiguration = RushConfiguration.loadFromDefaultLocation();
const project = rushConfiguration.findProjectByShorthandName('my-app');

if (project) {
  const packageJsonEditor = project.packageJsonEditor;
  
  // 添加依赖
  packageJsonEditor.addOrUpdateDependency('lodash', '4.17.21', 'dependencies');
  
  // 添加开发依赖
  packageJsonEditor.addOrUpdateDependency('@types/lodash', '4.14.0', 'devDependencies');
  
  // 保存修改
  packageJsonEditor.saveIfModified();
}
```

#### 依赖操作
```typescript
// 添加依赖
packageJsonEditor.addOrUpdateDependency(
  'package-name',     // 包名
  '1.0.0',           // 版本
  'dependencies'      // 依赖类型
);

// 删除依赖
packageJsonEditor.removeDependency('package-name');

// 更新依赖
packageJsonEditor.addOrUpdateDependency('package-name', '2.0.0', 'dependencies');

// 检查依赖是否存在
const hasDependency = packageJsonEditor.hasDependency('package-name');
```

#### 脚本管理
```typescript
// 添加脚本
packageJsonEditor.addOrUpdateScript('build', 'rushx build');
packageJsonEditor.addOrUpdateScript('test', 'rushx test');

// 删除脚本
packageJsonEditor.removeScript('build');

// 获取脚本
const buildScript = packageJsonEditor.getScript('build');
```

### 版本管理

#### 版本策略
```typescript
// 获取版本策略
const versionPolicies = rushConfiguration.versionPolicies;
for (const policy of versionPolicies) {
  console.log(`Policy: ${policy.policyName}`);
  console.log(`Type: ${policy.policyName}`);
}

// 查找版本策略
const policy = rushConfiguration.getVersionPolicy('my-policy');
if (policy) {
  console.log(`Policy found: ${policy.policyName}`);
}
```

#### 版本检查
```typescript
// 检查版本一致性
const versionMismatch = rushConfiguration.checkRushJsonMatchesPackageJson();
if (versionMismatch) {
  console.log('Version mismatch detected');
}
```

## 插件系统 API

### RushSession

#### 创建会话
```typescript
import { RushSession } from '@microsoft/rush-lib';

const rushSession = new RushSession({
  rushConfiguration: rushConfiguration
});
```

#### 生命周期钩子
```typescript
// 构建前钩子
rushSession.hooks.build.tap('my-plugin', (build) => {
  console.log('Before build');
});

// 构建后钩子
rushSession.hooks.build.tapAsync('my-plugin', (build, callback) => {
  console.log('After build');
  callback();
});

// 安装前钩子
rushSession.hooks.install.tap('my-plugin', (install) => {
  console.log('Before install');
});

// 安装后钩子
rushSession.hooks.install.tapAsync('my-plugin', (install, callback) => {
  console.log('After install');
  callback();
});
```

### 插件开发

#### 基础插件结构
```typescript
import { RushSession, RushConfiguration } from '@microsoft/rush-lib';

export class MyPlugin {
  public static pluginName: string = 'my-plugin';

  public apply(rushSession: RushSession): void {
    // 构建前钩子
    rushSession.hooks.build.tap('my-plugin', (build) => {
      console.log('Before build');
    });

    // 构建后钩子
    rushSession.hooks.build.tapAsync('my-plugin', (build, callback) => {
      console.log('After build');
      callback();
    });
  }
}
```

#### 高级插件
```typescript
export class AdvancedPlugin {
  public static pluginName: string = 'advanced-plugin';

  public apply(rushSession: RushSession): void {
    // 构建前钩子
    rushSession.hooks.build.tap('advanced-plugin', (build) => {
      const { rushConfiguration } = build;
      
      // 获取构建项目
      const projects = rushConfiguration.projects;
      console.log(`Building ${projects.length} projects`);
      
      // 自定义构建逻辑
      this.customBuildLogic(projects);
    });

    // 构建后钩子
    rushSession.hooks.build.tapAsync('advanced-plugin', (build, callback) => {
      console.log('Build completed');
      callback();
    });
  }

  private customBuildLogic(projects: RushProject[]): void {
    // 自定义构建逻辑
    for (const project of projects) {
      console.log(`Processing project: ${project.packageName}`);
    }
  }
}
```

## 构建系统 API

### 构建配置

#### 构建选项
```typescript
interface BuildOptions {
  parallelism?: number;           // 并行度
  incremental?: boolean;          // 增量构建
  force?: boolean;               // 强制构建
  verbose?: boolean;             // 详细输出
  projects?: string[];           // 指定项目
}
```

#### 构建执行
```typescript
// 构建所有项目
const buildResult = await rushSession.build({
  parallelism: 4,
  incremental: true
});

// 构建特定项目
const buildResult = await rushSession.build({
  projects: ['my-app'],
  parallelism: 2
});
```

### 依赖分析

#### 依赖图分析
```typescript
// 获取依赖图
const dependencyGraph = rushConfiguration.getProjectDependencyGraph();

// 获取项目依赖
const project = rushConfiguration.findProjectByShorthandName('my-app');
if (project) {
  const dependencies = dependencyGraph.getDependencies(project);
  console.log('Dependencies:', dependencies.map(p => p.packageName));
  
  const dependents = dependencyGraph.getDependents(project);
  console.log('Dependents:', dependents.map(p => p.packageName));
}
```

#### 循环依赖检测
```typescript
// 检测循环依赖
const cycles = dependencyGraph.getCircularDependencies();
if (cycles.length > 0) {
  console.log('Circular dependencies detected:');
  for (const cycle of cycles) {
    console.log('Cycle:', cycle.map(p => p.packageName));
  }
}
```

## 文件系统 API

### 文件操作

#### 文件路径管理
```typescript
import { FileSystem } from '@microsoft/rush-lib';

// 获取项目路径
const projectPath = rushConfiguration.getProjectPath('my-app');
console.log('Project path:', projectPath);

// 检查文件是否存在
const exists = FileSystem.exists(projectPath);
console.log('Project exists:', exists);

// 读取文件
const content = FileSystem.readFile(projectPath + '/package.json');
const packageJson = JSON.parse(content);
```

#### 目录操作
```typescript
// 创建目录
FileSystem.ensureFolder(projectPath + '/dist');

// 删除目录
FileSystem.deleteFolder(projectPath + '/temp');

// 复制目录
FileSystem.copyFolder(
  projectPath + '/src',
  projectPath + '/dist'
);
```

### 临时文件管理

#### 临时目录
```typescript
// 获取临时目录
const tempFolder = rushConfiguration.commonTempFolder;
console.log('Temp folder:', tempFolder);

// 获取项目临时目录
const projectTempFolder = rushConfiguration.getProjectTempFolder('my-app');
console.log('Project temp folder:', projectTempFolder);
```

#### 缓存管理
```typescript
// 获取构建缓存目录
const buildCacheFolder = rushConfiguration.buildCacheFolder;
console.log('Build cache folder:', buildCacheFolder);

// 清理缓存
FileSystem.deleteFolder(buildCacheFolder);
```

## 事件系统 API

### 事件钩子

#### 构建事件
```typescript
// 构建开始事件
rushSession.hooks.build.tap('my-plugin', (build) => {
  console.log('Build started');
});

// 构建完成事件
rushSession.hooks.build.tapAsync('my-plugin', (build, callback) => {
  console.log('Build completed');
  callback();
});
```

#### 安装事件
```typescript
// 安装开始事件
rushSession.hooks.install.tap('my-plugin', (install) => {
  console.log('Install started');
});

// 安装完成事件
rushSession.hooks.install.tapAsync('my-plugin', (install, callback) => {
  console.log('Install completed');
  callback();
});
```

### 自定义事件

#### 创建自定义事件
```typescript
// 创建自定义事件
const customEvent = new EventEmitter();

// 监听自定义事件
customEvent.on('custom-event', (data) => {
  console.log('Custom event received:', data);
});

// 触发自定义事件
customEvent.emit('custom-event', { message: 'Hello World' });
```

## 工具函数 API

### 字符串处理

#### 路径处理
```typescript
import { Path } from '@microsoft/rush-lib';

// 规范化路径
const normalizedPath = Path.convertToSlashes('/path/to/file');
console.log('Normalized path:', normalizedPath);

// 获取相对路径
const relativePath = Path.getRelativePath('/base/path', '/base/path/file');
console.log('Relative path:', relativePath);

// 检查路径是否在目录内
const isInside = Path.isUnderOrEqual('/path/to/file', '/path/to');
console.log('Is inside:', isInside);
```

#### 字符串工具
```typescript
import { StringBuffer } from '@microsoft/rush-lib';

// 创建字符串缓冲区
const buffer = new StringBuffer();
buffer.append('Hello');
buffer.append(' ');
buffer.append('World');
console.log('Buffer content:', buffer.toString());
```

### 日志系统

#### 日志记录
```typescript
import { ConsoleTerminalProvider, Terminal } from '@microsoft/rush-lib';

// 创建终端
const terminal = new Terminal(new ConsoleTerminalProvider());

// 记录日志
terminal.writeLine('Info message');
terminal.writeWarningLine('Warning message');
terminal.writeErrorLine('Error message');

// 设置日志级别
terminal.setVerbose(true);
```

#### 颜色输出
```typescript
// 彩色输出
terminal.writeLine('Success message', TerminalColor.Green);
terminal.writeLine('Error message', TerminalColor.Red);
terminal.writeLine('Warning message', TerminalColor.Yellow);
```

## 实用工具 API

### 项目分析

#### 依赖分析工具
```typescript
// 分析项目依赖
function analyzeDependencies(rushConfiguration: RushConfiguration) {
  const projects = rushConfiguration.projects;
  
  for (const project of projects) {
    console.log(`\nProject: ${project.packageName}`);
    console.log(`Dependencies: ${project.dependencyProjects.length}`);
    console.log(`Consumers: ${project.consumingProjects.length}`);
    
    // 分析依赖类型
    const dependencies = project.dependencyProjects;
    const internalDeps = dependencies.filter(p => p.packageName.startsWith('@tiktok/'));
    const externalDeps = dependencies.filter(p => !p.packageName.startsWith('@tiktok/'));
    
    console.log(`Internal dependencies: ${internalDeps.length}`);
    console.log(`External dependencies: ${externalDeps.length}`);
  }
}
```

#### 构建时间分析
```typescript
// 分析构建时间
function analyzeBuildTime(rushConfiguration: RushConfiguration) {
  const projects = rushConfiguration.projects;
  const buildTimes = new Map<string, number>();
  
  for (const project of projects) {
    const startTime = Date.now();
    
    // 执行构建
    // ... 构建逻辑 ...
    
    const endTime = Date.now();
    const buildTime = endTime - startTime;
    buildTimes.set(project.packageName, buildTime);
  }
  
  // 输出构建时间统计
  console.log('\nBuild time analysis:');
  for (const [projectName, buildTime] of buildTimes) {
    console.log(`${projectName}: ${buildTime}ms`);
  }
}
```

### 自动化脚本

#### 批量操作脚本
```typescript
// 批量更新依赖
async function batchUpdateDependencies(rushConfiguration: RushConfiguration) {
  const projects = rushConfiguration.projects;
  
  for (const project of projects) {
    console.log(`Updating dependencies for ${project.packageName}`);
    
    const packageJsonEditor = project.packageJsonEditor;
    
    // 更新特定依赖
    packageJsonEditor.addOrUpdateDependency('lodash', '4.17.21', 'dependencies');
    
    // 保存修改
    packageJsonEditor.saveIfModified();
  }
  
  console.log('Batch update completed');
}
```

#### 代码生成脚本
```typescript
// 生成项目报告
function generateProjectReport(rushConfiguration: RushConfiguration) {
  const projects = rushConfiguration.projects;
  const report = {
    totalProjects: projects.length,
    projects: []
  };
  
  for (const project of projects) {
    const projectInfo = {
      name: project.packageName,
      folder: project.projectRelativeFolder,
      shouldPublish: project.shouldPublish,
      dependencies: project.dependencyProjects.length,
      consumers: project.consumingProjects.length
    };
    
    report.projects.push(projectInfo);
  }
  
  // 输出报告
  console.log(JSON.stringify(report, null, 2));
}
```

## 错误处理 API

### 异常处理

#### 自定义异常
```typescript
class RushError extends Error {
  constructor(message: string, public projectName?: string) {
    super(message);
    this.name = 'RushError';
  }
}

// 使用自定义异常
function validateProject(project: RushProject): void {
  if (!project.packageName) {
    throw new RushError('Project name is required', project.packageName);
  }
}
```

#### 错误恢复
```typescript
// 错误恢复机制
function safeExecute<T>(operation: () => T, fallback: T): T {
  try {
    return operation();
  } catch (error) {
    console.error('Operation failed:', error);
    return fallback;
  }
}
```

### 日志记录

#### 结构化日志
```typescript
interface LogEntry {
  level: 'info' | 'warn' | 'error';
  message: string;
  projectName?: string;
  timestamp: Date;
}

class Logger {
  private logs: LogEntry[] = [];
  
  log(level: LogEntry['level'], message: string, projectName?: string): void {
    const entry: LogEntry = {
      level,
      message,
      projectName,
      timestamp: new Date()
    };
    
    this.logs.push(entry);
    console.log(`[${level.toUpperCase()}] ${message}`);
  }
  
  getLogs(): LogEntry[] {
    return this.logs;
  }
}
```

## 性能监控 API

### 性能指标

#### 构建性能监控
```typescript
class BuildPerformanceMonitor {
  private metrics: Map<string, number> = new Map();
  
  startTimer(projectName: string): void {
    this.metrics.set(`${projectName}-start`, Date.now());
  }
  
  endTimer(projectName: string): number {
    const startTime = this.metrics.get(`${projectName}-start`);
    if (startTime) {
      const endTime = Date.now();
      const duration = endTime - startTime;
      this.metrics.set(`${projectName}-duration`, duration);
      return duration;
    }
    return 0;
  }
  
  getMetrics(): Map<string, number> {
    return this.metrics;
  }
}
```

#### 内存使用监控
```typescript
// 监控内存使用
function monitorMemoryUsage(): void {
  const usage = process.memoryUsage();
  console.log('Memory usage:');
  console.log(`RSS: ${usage.rss / 1024 / 1024} MB`);
  console.log(`Heap Total: ${usage.heapTotal / 1024 / 1024} MB`);
  console.log(`Heap Used: ${usage.heapUsed / 1024 / 1024} MB`);
  console.log(`External: ${usage.external / 1024 / 1024} MB`);
}
```

## 相关资源

### 官方文档
- [Rush.js 官方文档](https://rushjs.io/)
- [Rush.js API 参考](https://rushjs.io/zh-cn/pages/extensibility/api/)
- [Rush.js 插件开发](https://rushjs.io/pages/maintainer/using_rush_plugins/)

### 示例代码
- [Rush.js 示例仓库](https://github.com/microsoft/rushstack)
- [插件开发示例](https://rushjs.io/pages/maintainer/using_rush_plugins/)

### 社区资源
- [Rush.js GitHub](https://github.com/microsoft/rushstack)
- [Rush.js 讨论区](https://github.com/microsoft/rushstack/discussions)
