# Dolphin SDK容灾方案

## 背景
Dolphin提供了SDK方案供业务接入，除了SDK从Dolphin通过RPC方式获取每个事件下的规则外，其余逻辑都在接入方执行。这样可能存在的问题是当Dolphin服务不能正常运行时，SDK无法获取到规则。当接入SDK的业务实例升级、重启等操作时，可能导致Dolphin SDK不可用。

## 目标
- Dolphin服务出现问题不会完全影响SDK的使用

## 方案概述
方案总体思路是将规则额外存储一份，在业务服务通过SCM打包时，获取规则备份文件，与业务服务集成到一起作为兜底，降低不可用的风险。

### TOS方式
1. 把所有SDK接入的event下所有规则生成文件存储到TOS中，TOS支持国内HTTP形式访问
2. 需要容灾的业务在build.sh中加入获取文件的命令，在SCM构建时将通过访问HTTP把兜底文件打包到接入方项目中
3. 接入dolphin-sdk的业务项目在启动时，SDK在通过RPC读取所有规则时，如果获取不到，解析兜底文件，加载规则；后续RPC调用正常后，继续更新规则

## 详细设计

### 规则组支持兜底版本
规则组本身目前存在版本概念，针对SDK接入的事件，默认采用当前使用版本的规则作为兜底。

### 规则备份流程
在admin对生效规则组进行变更时（包括修改规则、回滚版本等），会同步备份规则到TOS中。上线后会对历史接入的event进行一次生成操作。

**备份流程步骤：**
1. 查询出规则变更所属BizLine下所有的event
2. 针对每个需要备份的event，获取event下所有的规则组列表当前生效版本
3. 针对每个event，查询出所有的factor
4. 将规则组列表与factors一起拼成json数据，然后将json转为字节数组，写入到文件中（如果设置秘钥，对文件内容进行加密处理），文件同时包含规则组的版本号
   - 文件第一行存储MD5值，用于对文件内容进行校验
   - 之后的每一行为一个event的规则兜底数据

**JSON格式示例：**
```json
{
    "rule_groups":[
        {
            "rule":{
                "id":14128,
                "name":"数学及格",
                "expression":"math_score > 60",
                "bizline_id":2,
                "group_id":3422,
                "event_id":612
            },
            "decision":{
                "id":14106,
                "name":"",
                "operation":"SET",
                "config":"{\"kv\":{\"score\":\"60\"}}\n",
                "bizline_id":2,
                "event_id":612,
                "group_id":3422
            },
            "event_mapping":{
                "id":14139,
                "bizline_id":2,
                "event_id":612,
                "group_id":3422,
                "rule_id":14128,
                "decision_id":14106,
                "priority":1,
                "config":""
            },
            "priority":1,
            "mapping_id":14139,
            "group_version":"V4"
        }
    ],
    "factors":[
        {
            "id":10537,
            "name":"math_score",
            "f_type":"vl",
            "config":"{\"param_key\":\"math_score\"}",
            "ret_type":"number"
        }
    ]
}
```

5. 将文件上传到TOS，存储两份，TOS Key分别为 `bizline_name:timestamp` 和 `bizline_name:current`

### 备份文件加载
1. **文件获取**：接入SDK的业务在build.sh中新增获取备份文件的命令，通过curl把文件拉取到本地，与业务代码一起打包
2. **文件加载**：初始化SDK需要新增一个参数`backup_file_location`，SDK在启动时会去指定位置加载文件
   - 先对下载的文件进行md5校验、解密，如果校验、解密不通过，直接启动失败
   - 加载后作为兜底Conf保存在内存中
3. **数据打点**：SDK从内存获取规则数据时进行打点，用于判断是从RPC还是兜底文件（以及哪个版本）获取的规则数据

### 规则数据读取
SDK还是会正常通过RPC请求Dolphin获取ConfData，与备份的Conf是独立的两份数据。SDK在读取规则信息时，优先读取RPC获取的数据，当RPC ConfData为空时，才会去取备份Conf。当RPC可以正常获取Conf Data后，SDK会取用RPC的Conf数据。

## 注意事项
- 上线前，规则版本问题需要与业务方同步
