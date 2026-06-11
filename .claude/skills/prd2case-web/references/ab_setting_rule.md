# Experiment setting judgement and 


## Experiment Setting (A/B Settings) Types
  - [case1] No experiment: There is no experiment setting related information in the context. Including the case that there is only A/B Settings sections but no exact content
  - [case2] One experiment multi groups: The context typically does not explicitly state that there is only one experiment; instead, it directly lists the experiment groups and their logic.
  - [case3] Multi experiment multi groups: multi experiments, multi groups in each experiment.


## Framework for Different Experiment Types
- Note that the examples below are just to explain the basic structure of framework. Under each specific experiment group, 
- Based on the analysis result, organize your framework 

  - case1: No discussions about experiment settings
```
# 功能测试
// ... 直接开始测试场景梳理
```

  - case2: The group name must include the corresponding experiment group identifier (e.g., v0, v1, v2)
```
# 功能测试
## $分组名称1（比如v0）
### xxx
#### xxx 
**测试内容** xxx 
## $分组名称2（比如v1）
### xxx  
#### xxx 
**测试内容** xxx 
```

  - case3: For each experiment, the functional points should be expanded for every group.
```
# 功能测试
## 实验1: $实验内容
### $分组名称1
#### xxx  
##### xxx 
**测试内容** xxx 
### 实验2: $分组名称2
#### xxx 
##### xxx 
**测试内容** xxx 
...
## 实验2: $实验内容
### $分组名称1
#### xxx  
##### xxx 
**测试内容** xxx 
### $分组名称2
#### xxx  
##### xxx 
**测试内容** xxx 
...
```