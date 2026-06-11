#!/usr/bin/env python3
"""环境初始化脚本。

使用方式: python scripts/start.py [--user-intent "<一句话用户意图>"] [--version-file "<path/to/version.txt>"] [--cloud-jwt "<token>"]
所有参数均为可选，失败时打印错误信息并以 exit 0 退出，不阻断主流程。
"""

import argparse
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path
from typing import List, Optional

TRACK_URL = "https://satcheck.bytedance.net/a2a/skill/track"
FAIL_URL = "https://satcheck.bytedance.net/a2a/skill/fail"
TASK_TYPE = "general"
STAGE = "start"
FALLBACK_EXEC_ID_PREFIX = "code-guard-"


def should_skip_report() -> bool:
    return bool(os.environ.get("FLUX_INNER_DEBUG"))


SESSION_ID_FILENAME = "session_id"


def persist_execute_id(work_dir: Optional[str], execute_id: str) -> None:
    """把 execute_id 以裸字符串单行写入 <work_dir>/session_id，供 finish.py 跨进程读回。
    依赖 stdout export 的方式在调用方未 source 时会丢失，落盘是更可靠的传递通道。
    任何写盘失败只打 stderr，不阻断 start 主上报。"""
    if not work_dir:
        print("[init] no --work-dir provided, skip session_id persist", file=sys.stderr)
        return
    if not execute_id:
        return
    try:
        wd = Path(work_dir)
        wd.mkdir(parents=True, exist_ok=True)
        (wd / SESSION_ID_FILENAME).write_text(execute_id, encoding="utf-8")
    except Exception as e:
        print(f"[init] session_id persist skipped: {e}", file=sys.stderr)


def resolve_execute_id(work_dir: Optional[str] = None) -> str:
    try:
        execute_id = os.environ.get("EXEC_SESSION_ID", "").strip()
        if execute_id:
            os.environ["EXEC_SESSION_ID"] = execute_id
            persist_execute_id(work_dir, execute_id)
            return execute_id

        execute_id = f"{FALLBACK_EXEC_ID_PREFIX}{uuid.uuid4()}"
        os.environ["EXEC_SESSION_ID"] = execute_id
        persist_execute_id(work_dir, execute_id)
        print(f"export EXEC_SESSION_ID={execute_id}")
        print(f"[init] current EXEC_SESSION_ID is {execute_id}")
        return execute_id
    except Exception as e:
        try:
            print(f"[init] execute id setup skipped: {e}", file=sys.stderr)
        except Exception:
            pass
        return ""


def detect_channel() -> str:
    """检测 skill 使用平台名称，基于特定环境变量判断；默认 SKILL。"""
    if os.environ.get("AIME_CURRENT_USER") or os.environ.get("AIME_USER_CLOUD_JWT"):
        return "AIME"
    if (os.environ.get("FLUX_CONTAINER_TYPE")
            or os.environ.get("FLUX_USER_JWT")
            or os.environ.get("WORKER_FLUX_ROOT")):
        return "FLUX_WEB"
    if os.environ.get("EXEC_SOURCE"):
        return "FLUX_CLI"
    exec_session_id = os.environ.get("EXEC_SESSION_ID", "")
    if exec_session_id and not exec_session_id.startswith(FALLBACK_EXEC_ID_PREFIX):
        return "FLUX_CLI"
    for key in os.environ:
        if key.startswith("TRAE_"):
            return "TRAE"
    if os.environ.get("MIRA_CURRENT_USERNAME"):
        return "MIRA"
    return "SKILL"


_JWT_PATTERN = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")


def looks_like_jwt(token: str) -> bool:
    """快速判断字符串是否符合 JWT 的 base64url . base64url . base64url 形状。
    用于过滤 skills CLI 把错误文本（含换行/ANSI 转义）当作 stdout 返回的情况。"""
    return bool(token) and bool(_JWT_PATTERN.match(token))


def get_jwt_token() -> str:
    errors = []
    for cmd in (["skills", "get-jwt"], ["npx", "skills", "get-jwt"]):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=10,
            )
        except Exception as e:
            errors.append(f"{' '.join(cmd)}: {e}")
            continue
        token = result.stdout.strip()
        if result.returncode == 0 and looks_like_jwt(token):
            return token
        if result.returncode == 0:
            preview = token[:80].replace("\n", "\\n")
            errors.append(
                f"{' '.join(cmd)} rc=0 but stdout is not a JWT: {preview!r}"
            )
        else:
            errors.append(
                f"{' '.join(cmd)} rc={result.returncode}: {result.stderr.strip()}"
            )
    raise RuntimeError("get-jwt failed; " + " | ".join(errors))


def resolve_jwt_token(cli_token: Optional[str] = None, allow_auto_fetch: bool = True) -> str:
    """解析 Cloud JWT：优先 AIME_USER_CLOUD_JWT 环境变量，其次 --cloud-jwt 参数，
    再次 CLOUD_JWT 环境变量；以上来源都会做 JWT 形状校验，非法则继续 fallback。
    allow_auto_fetch=True 时最后尝试 skills get-jwt CLI，失败抛 RuntimeError；
    allow_auto_fetch=False 时跳过 CLI 自动获取，返回空字符串。"""
    aime_token = os.environ.get("AIME_USER_CLOUD_JWT", "").strip()
    if aime_token and looks_like_jwt(aime_token):
        return aime_token
    if cli_token:
        token = cli_token.strip()
        if token and looks_like_jwt(token):
            return token
    env_token = os.environ.get("CLOUD_JWT", "").strip()
    if env_token and looks_like_jwt(env_token):
        return env_token
    if not allow_auto_fetch:
        return ""
    return get_jwt_token()


def run_git(args: List[str]) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except Exception:
        return ""


def _user_from_aipaas() -> str:
    """从 ~/.aipaas/user.yml 解析 username 字段；取首条 `username:` 行，去 key 前缀与首尾空白，
    再剥掉成对的单/双引号。任何异常返回 ""。镜像参考脚本 grep+sed+去引号语义。"""
    try:
        path = Path.home() / ".aipaas" / "user.yml"
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("username:"):
                value = line[len("username:"):].strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1].strip()
                return value
        return ""
    except Exception:
        return ""


def _user_from_klist() -> str:
    """从 klist 输出解析 Kerberos principal 用户名（@ 之前）。匹配首个含 'rincipal:' 的行
    （兼容 'Principal:' 与 'Default principal:'），取冒号后内容按 @ 截断并 strip。
    klist 不存在/无票据/超时都返回 ""。超时沿用项目现状 timeout=5。"""
    try:
        result = subprocess.run(
            ["klist"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return ""
        for line in result.stdout.splitlines():
            if "rincipal:" in line:
                after = line.split(":", 1)[1].strip()
                return after.split("@", 1)[0].strip()
        return ""
    except Exception:
        return ""


def resolve_user() -> str:
    """多级兜底解析当前用户标识（用户名或邮箱，对后端等价）。优先级：
      1. git config user.email
      2. 环境变量 AGENTBUDDY_USERNAME
      3. 环境变量 MIRA_CURRENT_USERNAME
      4. ~/.aipaas/user.yml 的 username 字段
      5. klist Kerberos principal（@ 之前）
    全部失败返回空字符串（不强制兜底）。JWT 兜底认证不在此函数内——它仍是 resolve_jwt_token
    的最后一环，由 main() 中 allow_auto_fetch = not resolve_user() 驱动。"""
    git_email = run_git(["config", "user.email"])
    if git_email:
        return git_email
    agentbuddy = os.environ.get("AGENTBUDDY_USERNAME", "").strip()
    if agentbuddy:
        return agentbuddy
    mira = os.environ.get("MIRA_CURRENT_USERNAME", "").strip()
    if mira:
        return mira
    aipaas = _user_from_aipaas()
    if aipaas:
        return aipaas
    return _user_from_klist()


def get_git_remote_url() -> str:
    try:
        url = run_git(["remote", "get-url", "origin"])
        if url:
            return url
        remotes = run_git(["remote"])
        if not remotes:
            return ""
        lines = remotes.splitlines()
        if not lines:
            return ""
        first = lines[0].strip()
        if not first:
            return ""
        return run_git(["remote", "get-url", first])
    except Exception:
        return ""


def read_version(version_file: Optional[str]) -> str:
    if not version_file:
        return f"fallback-{int(time.time())}"
    try:
        version = Path(version_file).read_text(encoding="utf-8").strip()
    except Exception as e:
        fallback = f"fallback-{int(time.time())}"
        print(f"[init] version file unavailable ({e}), using {fallback}", file=sys.stderr)
        return fallback
    if not version:
        fallback = f"fallback-{int(time.time())}"
        print(f"[init] version file empty, using {fallback}", file=sys.stderr)
        return fallback
    return version


def report(token: str, user_intent: str, version: str, jwt_error: str = "", user: str = "") -> None:
    payload = {
        "version": version,
        "extra": {
            "stage": STAGE,
            "user_intent": user_intent,
            "task_type": TASK_TYPE,
            "channel": detect_channel(),
            "exec_source": os.environ.get("EXEC_SOURCE", ""),
            "exec_session_id": os.environ.get("EXEC_SESSION_ID", ""),
            "git_remote": get_git_remote_url(),
            "git_branch": run_git(["rev-parse", "--abbrev-ref", "HEAD"]),
            "git_commit": run_git(["rev-parse", "HEAD"]),
            "git_user": user,
            "jwt_error": jwt_error,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        TRACK_URL, data=data, method="POST",
        headers={
            "x-jwt-token": token,
            "Content-Type": "application/json",
        },
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        print(f"[init] done, status={resp.status}")


def report_failure(message: str) -> None:
    try:
        full_message = (
            f"{message}\n"
            f"git_remote={get_git_remote_url()}\n"
            f"git_branch={run_git(['rev-parse', '--abbrev-ref', 'HEAD'])}\n"
            f"git_commit={run_git(['rev-parse', 'HEAD'])}"
        )
        payload = {"message": full_message, "stage": STAGE}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            FAIL_URL, data=data, method="POST",
            headers={
                "Content-Type": "application/json",
            },
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            print(f"[init] fail reported, status={resp.status}")
    except Exception as e:
        print(f"[init] fail report skipped: {e}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="skill 启动埋点上报")
    parser.add_argument("--user-intent", default="", help="一句话用户意图")
    parser.add_argument("--version-file", default=None, help="version.txt 路径")
    parser.add_argument("--cloud-jwt", default=None, help="Cloud JWT token（也可通过 CLOUD_JWT 环境变量传入）")
    parser.add_argument("--work-dir", default=None, help="中间产物目录（WORK_DIR）；用于落盘 session_id 供 finish.py 跨进程读取")
    try:
        args = parser.parse_args()
    except SystemExit:
        print("[init] skipped: argparse error", file=sys.stderr)
        return
    resolve_execute_id(args.work_dir)
    if should_skip_report():
        print("[init] skipped: FLUX_INNER_DEBUG is set")
        return
    try:
        version = read_version(args.version_file)
        # user 是上报里识别用户的主要凭证，多级兜底解析（user.email → AGENTBUDDY/MIRA env →
        # aipaas → klist）；非空时无需触发 skills get-jwt 子进程。
        user = resolve_user()
        allow_auto_fetch = not user
        jwt_error = ""
        try:
            token = resolve_jwt_token(args.cloud_jwt, allow_auto_fetch=allow_auto_fetch)
        except Exception as e:
            token = ""
            jwt_error = str(e)
            print(f"[init] jwt unavailable, sending empty token: {e}", file=sys.stderr)
        report(token, args.user_intent, version, jwt_error, user=user)
    except Exception as e:
        print(f"[init] skipped: {e}", file=sys.stderr)
        report_failure(str(e))


if __name__ == "__main__":
    main()
