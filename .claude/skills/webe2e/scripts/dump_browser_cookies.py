#!/usr/bin/env python3
"""
Optional helper: dump browser cookies for a specific domain into a Netscape
cookies.txt file that downstream auth-aware steps (TDRS API queries,
playwright-cli execution, etc.) and `tdrs_preflight.py` can consume.

This script is opt-in: nothing calls it automatically. Users run it when they
want to skip the manual "export cookies" step before starting webe2e
execution or TDRS data research.

Design constraints:
- `browser_cookie3` is NOT auto-installed when missing. The script prints two
  explicit install commands and exits 2. The user decides which environment
  to install into.
- `--domain` is required and trimmed; an empty/whitespace value is rejected.
- The written file is chmod 0600 to avoid leaking session cookies.
- `--print-only` lists cookie names without writing the file (useful for the
  user to confirm scope before persisting credentials).

Usage:
    python3 dump_browser_cookies.py --domain example.com [--browser chrome]
                                    [--out cookies.txt] [--print-only]
"""

from __future__ import annotations

import argparse
import http.cookiejar
import os
import stat
import sys
from pathlib import Path
from typing import Any, Optional, Sequence


INSTALL_HINT = (
    "browser_cookie3 is not installed. This script does NOT auto-install. "
    "Pick one and run it yourself:\n"
    "  pipx install browser_cookie3            # recommended, isolated env\n"
    "  python3 -m pip install --user browser_cookie3   # alternative, user site"
)

SUPPORTED_BROWSERS = ("chrome", "chromium", "edge", "firefox", "safari", "brave", "opera")


def _import_browser_cookie3() -> Optional[Any]:
    try:
        import browser_cookie3  # type: ignore
    except ImportError:
        return None
    return browser_cookie3


def _fetch_jar(module: Any, browser: str, domain: str) -> Any:
    reader = getattr(module, browser, None)
    if reader is None:
        raise RuntimeError(f"browser_cookie3 has no `{browser}` reader.")
    return reader(domain_name=domain)


def _filter_by_domain(jar: Any, domain: str) -> list[Any]:
    needle = domain.lstrip(".").lower()
    cookies: list[Any] = []
    for cookie in jar:
        host = (getattr(cookie, "domain", "") or "").lstrip(".").lower()
        if not host:
            continue
        if host == needle or host.endswith("." + needle) or needle.endswith("." + host):
            cookies.append(cookie)
    return cookies


def _write_netscape(out_path: Path, cookies: Sequence[Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    jar = http.cookiejar.MozillaCookieJar(str(out_path))
    for cookie in cookies:
        jar.set_cookie(cookie)
    jar.save(ignore_discard=True, ignore_expires=True)
    os.chmod(out_path, stat.S_IRUSR | stat.S_IWUSR)


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Dump browser cookies for a domain in Netscape format. "
            "Requires browser_cookie3 (installed by the user, not by this script)."
        )
    )
    parser.add_argument("--domain", required=True, help="Target domain to scope cookies, e.g. example.com.")
    parser.add_argument(
        "--browser",
        default="chrome",
        choices=SUPPORTED_BROWSERS,
        help="Browser store to read from.",
    )
    parser.add_argument("--out", default="cookies.txt", help="Output cookies.txt path.")
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="List the cookies that would be exported without writing the output file.",
    )
    return parser.parse_args(argv)


def run(
    argv: Optional[Sequence[str]] = None,
    *,
    module: Any = None,
    _force_missing: bool = False,
) -> int:
    args = parse_args(argv)

    domain = (args.domain or "").strip()
    if not domain:
        print("--domain must be a non-empty hostname (e.g. example.com).", file=sys.stderr)
        return 2

    bc3 = None if _force_missing else (module if module is not None else _import_browser_cookie3())
    if bc3 is None:
        print(INSTALL_HINT, file=sys.stderr)
        return 2

    try:
        jar = _fetch_jar(bc3, args.browser, domain)
    except Exception as exc:
        print(f"failed to read cookies from {args.browser}: {exc}", file=sys.stderr)
        return 3

    cookies = _filter_by_domain(jar, domain)
    if not cookies:
        print(
            f"no cookies found for domain `{domain}` in {args.browser}; "
            "open the site in that browser, log in, then re-run.",
            file=sys.stderr,
        )
        return 4

    if args.print_only:
        for cookie in cookies:
            host = getattr(cookie, "domain", "?") or "?"
            name = getattr(cookie, "name", "?") or "?"
            print(f"{host}\t{name}")
        return 0

    out_path = Path(args.out)
    _write_netscape(out_path, cookies)
    print(f"wrote {len(cookies)} cookie(s) to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
