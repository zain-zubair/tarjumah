"""claude -p subprocess wrapper. Subscription-absorbed (NOT API-billed).

Do NOT add --bare; that forces API-key auth and breaks our cost model.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "claude-opus-4-7"
LONG_CONTEXT_MODEL = "claude-opus-4-7[1m]"
FAST_MODEL = "claude-sonnet-4-6"

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_LOG = _PROJECT_ROOT / "data" / "runs.jsonl"


def run_claude(
    prompt: str,
    model: str = DEFAULT_MODEL,
    timeout: int = 600,
    retries: int = 2,
    expect_json: bool = False,
    cwd: str | None = None,
) -> Any:
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        started = time.time()
        try:
            r = subprocess.run(
                ["claude", "-p", "--model", model, "--no-session-persistence", prompt],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd or str(_PROJECT_ROOT),
            )
            duration = time.time() - started
            if r.returncode != 0:
                last_err = RuntimeError(f"claude -p exit {r.returncode}: {r.stderr[:500].strip()}")
                _log("error", model, len(prompt), 0, duration, str(last_err))
            else:
                out = r.stdout.strip()
                _log("ok", model, len(prompt), len(out), duration, None)
                if expect_json:
                    return _parse_json(out, prompt, model, timeout)
                return out
        except subprocess.TimeoutExpired:
            duration = time.time() - started
            last_err = TimeoutError(f"claude -p timeout after {timeout}s")
            _log("timeout", model, len(prompt), 0, duration, str(last_err))
        except FileNotFoundError as e:
            _log("missing-cli", model, len(prompt), 0, 0, str(e))
            raise RuntimeError("`claude` CLI not found on PATH. Install Claude Code first.") from e
        except Exception as e:
            duration = time.time() - started
            last_err = e
            _log("exception", model, len(prompt), 0, duration, str(e))
        if attempt < retries:
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"claude -p failed after {retries + 1} attempts: {last_err}")


def _parse_json(text: str, original_prompt: str, model: str, timeout: int) -> Any:
    parsed = _try_parse(text)
    if parsed is not None:
        return parsed
    fix_prompt = (
        "Your previous response was not valid JSON. Return ONLY valid JSON — no prose, no code fences, no commentary. "
        "Begin with `{` or `[`.\n\nOriginal task (for reference):\n" + original_prompt[:8000]
    )
    r = subprocess.run(
        ["claude", "-p", "--model", model, "--no-session-persistence", fix_prompt],
        capture_output=True, text=True, timeout=timeout,
        cwd=str(_PROJECT_ROOT),
    )
    if r.returncode == 0:
        parsed2 = _try_parse(r.stdout.strip())
        if parsed2 is not None:
            return parsed2
    raise ValueError(f"Could not extract JSON. First 500 chars of output: {text[:500]}")


def _try_parse(text: str) -> Any:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    if cleaned.startswith(("{", "[")):
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            return None
    return None


def run_claude_parallel(
    prompts: list[str],
    model: str = DEFAULT_MODEL,
    max_workers: int = 5,
    timeout: int = 600,
    expect_json: bool = False,
) -> list[Any]:
    results: list[Any] = [None] * len(prompts)
    errors: dict[int, Exception] = {}

    def _one(i: int) -> None:
        try:
            results[i] = run_claude(prompts[i], model=model, timeout=timeout, expect_json=expect_json)
        except Exception as e:
            errors[i] = e

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        list(ex.map(_one, range(len(prompts))))

    if errors:
        first_idx = min(errors)
        raise errors[first_idx]
    return results


def _log(status: str, model: str, in_chars: int, out_chars: int, duration: float, err: str | None) -> None:
    try:
        RUNS_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "model": model,
            "in_chars": in_chars,
            "out_chars": out_chars,
            "duration_s": round(duration, 2),
            "error": err,
        }
        with RUNS_LOG.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
