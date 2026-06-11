# GuluX 配置管理指南

## 概述

GuluX框架提供了灵活的配置管理机制，支持多环境配置、动态配置加载和深度合并等功能。配置管理是GuluX应用开发的核心部分，帮助开发者管理不同环境下的应用配置。

## 运行环境配置

### 环境变量设置
GuluX通过`GULUX_ENV`环境变量来指定程序的运行环境，框架会根据运行环境加载相应的配置文件并进行合并。

```typescript
GULUX_ENV=dev
```

**默认值为default**，业务可以根据需求自定义这个值，在应用内可以通过`app.guluxEnv`来访问。

### 常用环境定义
- **dev**：本地开发环境
- **test**：运行单元测试的环境  
- **boe**：测试环境，对应BOE
- **prod**：线上生产环境，对应TCE

> **重要提示**：GuluX没有采用社区约定的NODE_ENV环境变量来当做运行环境的设置，主要是因为一些社区的库会通过NODE_ENV来判断是否运行DEBUG模式，所以线上环境请一定将NODE_ENV设置为production。

## 配置文件结构

### 配置文件命名规范
配置文件的命名遵循以下格式：
```bash
${配置组织方式}.${配置用途}.${后缀名}
```

### 配置组织方式
1. **聚合型配置**：文件名以`config`开头，将多个配置项收拢到一个文件中
2. **离散型配置**：文件名以配置项的名称开头，每个文件维护一个配置项

### 配置用途分类
1. **默认配置**：文件名的中间部分为`default`
2. **环境配置**：文件名的中间部分为对应的环境名称

### 目录结构示例
```bash
└── config
    ├── config.default.js      # 聚合型默认配置
    ├── redis.default.js       # 离散型默认配置
    ├── config.dev.js          # 聚合型环境配置
    └── redis.dev.js           # 离散型环境配置
```

## 配置编写方式

### 聚合型配置写法

#### 方法一：导出配置生成函数（动态配置）
```typescript
// config.default.ts
import {GuluXApplication, ApplicationConfig} from '@gulux/gulux';
export default (app: GuluXApplication) => {
  return {
    middleware: ['koa-body'],
    plugin: ['@gulux/runtime-base'],
    koaBody: {},
  } as ApplicationConfig;
};
```

#### 方法二：导出配置对象（静态配置）
```typescript
// config.default.ts
module.exports = {
  middleware: ['koa-body'],
  plugin: ['@gulux/runtime-base'],
  koaBody: {},
};
```

### 离散型配置写法
```typescript
// redis.default.js
module.exports = {
  host: '10.1.1.1',
  port: 6380,
};
```

**注意**：离散型配置文件命名遵循`${configKey}.${env}.ts`规则，前缀需为配置名。

## 配置合并规则

### 优先级规则
应用、插件都可以定义配置，但存在优先级，相对于此运行环境的优先级会更高。

例如当`GULUX_ENV=prod`环境时，`config.prod`比`config.default`优先级更高，配置合并时会以`config.prod`里面的内容优先。

### 合并示例
```typescript
// config.default.ts
export default {
  foo: 'bar'
}

// config.prod.ts
export default {
  foo: 'bar1'
}

// 合并后为
config = {
  foo: 'bar1'
}
```

### 深度合并
配置的深度合并采用[deepmerge](https://github.com/TehShrike/deepmerge)进行。**值得注意的是对于数组项的合并，框架采用了直接替换的方式**，因为数组元素之间往往存在顺序的要求，直接合并可能会导致与预期不符的结果 。

### 完整合并示例
```typescript
// config.default.ts
export default {
  psm: 'p.s.m',
  middleware: ['a'],
  redis: {
    host: '10.1.1.1',
    port: 6379,
  },
};

// redis.default.ts
export default {
  host: '10.1.1.1',
  port: 6380,
};

// config.dev.ts
export default {
  middleware: ['b'],
  redis: {
    host: '10.1.1.2',
    port: 6379,
  },
};

// redis.dev.js
export default {
  host: '10.1.1.2',
  port: 6380,
};
```

如果`GULUX_ENV=dev`，那么合并后的配置是：
```typescript
{
  psm: 'p.s.m',
  middleware: ['b'],
  redis: {
    host: '10.1.1.2',
    port: 6380,
  },
}
```

## 高级环境配置

### 多值环境变量
GuluX支持声明格式如下的多值环境变量：
```bash
_GULUX_ENV_=_${name}_:_${value1}_,_${value2}_,_${value3}_,...
```

`name`表示运行环境的名称，`value1`、`value2`、`value3`、...表示运行环境的具体组成部分，框架会根据这些值来加载环境配置，配置合并优先级为`value1` < `value2` < `value3` < ...。

### 使用场景示例

#### 场景1：脚本任务配置
```bash
├── config
|    ├── config.default.js # 默认配置
|    ├── config.dev.js     # 开发环境配置
|    ├── config.prod.js    # 生产环境配置
└──└── config.script.js  # 脚本环境配置
```

- 在开发环境下运行脚本：`GULUX_ENV=dev-script:dev,script`
- 在生产环境下运行脚本：`GULUX_ENV=prod-script:prod,script`

#### 场景2：机房专用配置
```bash
├── config
|   ├── config.default.js # 默认配置
|   ├── config.prod.js     # 生产环境配置
|   ├── config.CN.js     # 中国区公共配置
|   ├── config.lf.js    # 廊坊机房专用配置
└── └── config.hl.js  # 怀来机房专用配置
```

- 在`lf`机房指定：`GULUX_ENV=prod-lf:prod,CN,lf`
- 在`hl`机房指定：`GULUX_ENV=prod-hl:prod,CN,hl`

## 获取配置

GuluX框架会把合并后的配置挂载到应用实例上，可以通过`app.config`或`Config`装饰器进行访问。

### 使用示例
```typescript
import { GuluXApplication, Inject, Config, ApplicationConfig } from '@gulux/gulux';
import { Controller, Get } from '@gulux/gulux/application-http';

@Controller('/user')
export default class UserController {
  @Inject()
  public app: GuluXApplication;
  
  @Config()
  public config: ApplicationConfig;
  
  @Config('psm')
  public psm: string;
  
  @Get('/userlist')
  public async getUserList() {
    console.log(this.app.config.psm);
    console.log(this.config.psm);
    console.log(this.psm);
  }
}
```

## 特殊配置文件说明

### plugin配置文件
在配置文件中`plugin.default.ts`以及`plugin.${env}.ts`是比较特殊的配置文件，plugin的启用和包配置需要写在这里。

**注意**：plugin配置仅用于配置插件的启用和指定包名/路径，详细配置需参考插件文档在主配置中配置对应字段。

### middleware配置
配置中的`middleware`选项只能在项目中配置，不能出现在插件的配置文件中。

## 平台部署配置

字节内部平台部署时配置`GULUX_ENV`参考：[GULUX_ENV 配置 & auto env](https://bytedance.feishu.cn/wiki/wikcnuIm3qOiexMhGf6iAaRN7hd) 。

### TCE环境配置
在TCE中设置GULUX_ENV环境变量：
1. 点击集群**编辑**按钮，进入集群编辑页
2. 切换到**环境变量、Sidecar & 高级配置**选项
3. 添加环境变量GULUX_ENV

![TCE环境变量配置](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/9a10018b38764c96b931ad9611f5dad9~tplv-tika-image.image) 

### Stack环境配置
在Stack中设置GULUX_ENV环境变量：
1. 点击**设置 -> 环境变量**
2. 添加一个新的环境变量GULUX_ENV

![Stack环境变量配置](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/0e87baca89e44c23b9c1406d5e01a6d9~tplv-tika-image.image) 

### Deploy环境配置
在Deploy中设置GULUX_ENV环境变量：
1. 点击**设置 -> 部署能力**
2. 添加一个新的环境变量GULUX_ENV

![Deploy环境变量配置](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/4eed041b1e1747fe9e539b3428cd10b8~tplv-tika-image.image) 

## 最佳实践

### 配置组织建议
1. **按功能模块划分**：将相关配置放在一起，便于维护
2. **环境隔离**：确保不同环境的配置完全隔离
3. **敏感信息保护**：敏感配置不应提交到代码仓库

### 性能考虑
配置多个value的环境变量会影响启动性能，value数量越多，其配置/插件差异越大，影响越大。

### 文档参考
- GuluX官方文档站：https://gulux.bytedance.net/guide/basic/config/env-config.html
- 飞书文档（不再更新）：https://bytedance.feishu.cn/wiki/wikcnCpcPhDMSI80db1s19uVY9J

## 常见问题

### Q: 为什么GuluX不使用NODE_ENV作为运行环境变量？
A: 因为一些社区的库会通过NODE_ENV来判断是否运行DEBUG模式，所以线上环境请一定将NODE_ENV设置为production，而使用独立的GULUX_ENV来管理应用运行环境。

### Q: 如何在不同机房使用不同的配置？
A: 可以使用多值环境变量功能，创建机房专用配置文件，并通过`GULUX_ENV=prod-lf:prod,CN,lf`这样的格式指定。

### Q: 插件配置应该放在哪里？
A: 插件的启用和包配置需要写在`plugin.default.ts`或`plugin.${env}.ts`中，而插件的详细配置需要在主配置文件中配置对应字段。

## 总结

GuluX的配置管理系统提供了强大的多环境支持、灵活的配置合并机制和便捷的配置访问方式。通过合理使用聚合型和离散型配置，结合多值环境变量功能，可以构建出既灵活又易于维护的配置体系，满足企业级应用开发的复杂需求。