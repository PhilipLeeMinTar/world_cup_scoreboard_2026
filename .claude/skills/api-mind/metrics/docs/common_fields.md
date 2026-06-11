# metrics 公共字段

本文件仅在 `scripts/build_common_metrics.py` 无法满足字段写入、需要确认字段含义时读取。常规流程必须直接调用脚本；缓存完整时脚本会直接复用缓存，不得为了公共字段重复读取上下文或重复执行命令。

## 字段表

| 字段 | 类型 | 含义 | 获取方式 |
| --- | --- | --- | --- |
| `user_name` | string | 当前用户名 | 优先取会话内存 JWT，按 `header.payload.signature` 拆分后 base64-url 解码 payload 段，取 `username` 字段；仅会话尚无 JWT 时才执行一次 `gdpa-cli login -p cn` |
| `spec_name` | string | 当前特性目录名 | 脚本从 `<FEATURE_DIR>/test/.api-mind` 反推 `FEATURE_DIR` 后取 basename；必要时用 `--spec-name` 覆盖 |
| `psm` | string[] | 本次涉及的全部被测 PSM 列表 | 优先使用脚本参数 `--psm`；未传时脚本轻量读取 `FEATURE_DIR/test/task.md`，缺失时从 `case.md` 有限字节兜底提取 |
| `repo_name` | string | 仓库名 | 脚本仅在缓存缺失 / 不完整时执行 `git rev-parse --show-toplevel` 并取 basename |
| `repo_link` | string | 仓库远端链接 | 脚本仅在缓存缺失 / 不完整时执行 `git remote get-url origin` |

## 写入规则

```text
任意子任务 start hook 后：
  python3 metrics/scripts/build_common_metrics.py --workdir <工作目录>/.api-mind --user-name <username>

脚本内部：
  if exists(.api-mind/metrics_common.json) 且 5 字段完整:
      直接拷入 metrics.json 并结束公共字段采集
  else:
      从参数 / 有限字节文件 / git 最小命令采集 5 字段
      写入 .api-mind/metrics_common.json
      再拷入 metrics.json
```

注意：

- `user_name` 的来源统一为 `gdpa-cli login -p cn` JWT payload，不再使用 `gdpa-cli login -u cn`。
- 公共字段采集不得由模型完整阅读 `case.md` / `spec.md`；`psm` 交给脚本从 `test/task.md` / `case.md` 有限字节提取，或由主流程传入已有内存 PSM。
- `repo_name` / `repo_link` 只在缓存缺失时执行 git 命令；缓存存在时不得重复执行。
