# Forms and Grammar of Test Case

## Overall definition
- At its core, a test case can be represented as a tree data structure.
- In test case generation, test cases are represented in two formats: a text-based format (Markdown-like) and a structured JSON format.

## 1. Common Grammar
1. Key attributes of test case node: 
  - Node type: ENUM, only values below are allowed(Chinese only, DO NOT translate even in English test cases)
    - 测试点
    - 用例标题
    - 前置条件
    - 操作步骤
    - 预期结果
    - 测试内容(special node, only for text-based format)
  - Node content: content of the node, text
  - Node level: for text-based only. JSON format naturally contains the level information.

2. Node Regulation
  - The top-down order of test case is: `测试点` -> `用例标题`(optional) -> `前置条件` -> `操作步骤` -> `预期结果`
  - `用例标题` is optional, and should only be used when READING a test case, **DO NOT generate a node with type `用例标题`**.
  - Clarification: this restriction is about node type only. A node's text content can still be "用例标题" if its actual node type is not `用例标题`.
  - child of `测试点` must be either `测试点`, `前置条件`, `测试内容`(special node for framework generation) or `用例标题`(reading only)
  - child of `前置条件` must be `操作步骤`
  - child of `操作步骤` must be either `操作步骤`, `预期结果`
  - leaf node must be `预期结果` or `测试内容`(framework generation only)

3. Special Regulations 
  a. First child of `操作步骤` node should be `预期结果` and CANNOT be another `操作步骤`. If you want to describe a sequence of operations, group them in a single `操作步骤` node and separated using numbered lines with line breaks.

## 2. Grammar for text-based format

Example
```text
# 【酒旅C端】售中阶段客服入口逻辑优化
## 功能测试
**[hyperlink]** [超链接标题](url链接)
### 白名单商家商品（售中阶段）
**[tag]** 标签1,标签2,标签3
#### 不区分服务单状态调整
##### 右上角客服
###### **前置条件** 1. 商品为度假预售券商品
2. 商家为白名单试点商家 
3. 订单处于售中阶段（服务单状态：20-支付成功、50-待接单）
**[priority]** P2
**[tag]** 标签1,标签2,标签3
####### **操作步骤** step1-1
######## **预期结果** assertion1
######## **操作步骤** step1-1-next
######### **预期结果** assertion-1-next
####### **操作步骤** step1-2
######## **预期结果** assertion2-1
######## **预期结果** assertion2-2
```


1. Overall structure: text-based test case is multi-row Markdown-like text. The basic unit is a row.
2. Test case node: A node always starts with one or more `#` and ends before the first `#` of next node or end of file.
3. The number of `#` represents the level of the node.
4. Parent, child and sibling nodes:
  - Parent node should have exactly one less `#` than the child node
  - In the example:
    - step1-1 and step1-2 are both children of the `前置条件` node, they are sibling nodes, which means they are independent operations instead of sequential operations.
    - step1-2 has two children, the two assertions are sibling nodes
5. The **NODE_TYPE** right after `#` represents the node type:
  - `功能点` type: no identifier
  - others: 用例标题/前置条件/操作步骤/预期结果
  - Important: "do not generate `用例标题`" means do not generate NODE_TYPE=`用例标题`; it does not prohibit using the string "用例标题" as plain node content.
6. Other attributes of the node(each attribute should star a new line)
  - Priority: `**[priority]** P0`, support P0/P1/P2/P3
  - Tags: `**[tag]** 标签1,标签2,标签3`, use `,` to separate multiple tags
  - Hyperlink: `**[hyperlink]** [title](url)`
7. Special node type: `测试内容`
  - This node is a special node that ALWAYS attached to a leaf `功能点` node, and thus it SHOULD NOT start with `#`
  - A `测试内容` node is used in framework generation, and the content is 
  - example
```text
# 用例标题
## 功能
### 场景1
**测试内容** 这个场景下要测什么内容
### 场景2
**测试内容** 这个场景下要测什么内容
...
## 功能
...
```
8. example for common group 3-a (how to organize sequence of operations)

```text
...
#### **操作步骤** 1. step1
2. step2
3. step3
##### **预期结果** xxx
...
```


## 3. Grammar for JSON format
1. Core node shape (tree):
```json
{
  "data": {
    "text": "node content",
    "nodeType": 0,
    "priority": 0,
    "resource": ["标签1", "标签2"],
    "hyperlink": "https://example.com",
    "hyperlinkTitle": "链接标题"
  },
  "children": [
    {
      "data": { "...same shape..." },
      "children": null
    }
  ]
}
```

2. Fields that MUST be parsed (fields that occurred in Markdown format):
  - `data.text`: node content text
  - `data.nodeType`: node type (integer enum)
  - `data.priority`: priority code. `99` means `P0`; `0` means no priority tag.
  - `data.resource`: tags list, corresponding to `**[tag]** 标签1,标签2`
  - `data.hyperlink`: hyperlink URL, corresponding to `**[hyperlink]** [title](url)`
  - `data.hyperlinkTitle`: hyperlink title
  - `children`: child node list, recursive tree structure (`null` or `[]` means no child)

3. Node type mapping (for parser normalization):
```json
{
  "0": "功能点",
  "2": "功能点",
  "3": "前置条件",
  "4": "预期结果",
  "5": "操作步骤",
  "6": "操作步骤",
  "12": "用例标题",
  "13": "预期结果"
}
```

4. Optional fields (keep as passthrough; do not require parser to consume now):
  - `id`, `created`, `note`, `image`, `imageSize`, `progress`
  - `script_task`, `parentID`, `attachment`, `genId`, `createdBy`, `updatedBy`
