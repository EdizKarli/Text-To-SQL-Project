"""
run_with_model.py: runs Ediz's Spider 1.0 dev scripts with another Ollama model.

The prompts and the logic stay exactly as Ediz wrote them. His script runs unchanged
from his folder; only the model name in each Ollama request is replaced. This is the
same idea as Yiğit's run_with_model.py for BIRD (PR #7). In addition, for every question
this script saves:
  - Ollama's timing and token counts (total_duration, prompt_eval_count, eval_count, ...),
  - the raw model answer, before Ediz's sanitize_sql() cleans it (for error analysis).

The raw log gets one line per question as the run goes. If a run is interrupted, run the
same command again: questions already in the log are replayed from it, and the run
continues where it stopped.

Usage (from any folder, after the setup in README.md):
  python run_with_model.py --model qwen2.5-coder:1.5b --variant schema
  python run_with_model.py --model qwen2.5-coder:1.5b --variant schema --limit 5   (smoke test)

Variants: schema | pruned
"""
import argparse
import csv
import ctypes
import hashlib
import json
import os
import platform
import re
import runpy
import statistics
import subprocess
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EDIZ_DIR = os.path.join(REPO, "experiment_results", "spider", "ediz", "sevenB_parameter")
# 127.0.0.1, not localhost: on Windows, localhost resolves to IPv6 ::1 first, Ollama listens on IPv4 only,
# and Windows waits about 2 s before falling back. That added 2 s to every request on Basil's laptop.
OLLAMA = "http://127.0.0.1:11434"
BENCHMARK = "Spider 1.0 dev"

# variant -> (Ediz's script, the file it writes into the working folder)
SCRIPTS = {
    "schema": ("spider_infer_schema.py", "predict_spider.sql"),
    "pruned": ("spider_infer_pruned.py", "predict_spider_pruned.sql"),
}

TIMING_FIELDS = ("total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration",
                 "eval_count", "eval_duration", "done_reason")


class StopRun(BaseException):
    """Ends a --limit run. Ediz's scripts catch Exception, so this one gets through."""


def fill_empty_lines(pred_path, expected):
    """Both Spider evaluators pair predictions with gold queries by line, and they skip empty
    lines (or treat them as separators). One empty answer would shift every later prediction
    onto the wrong gold query. So empty answers are written as SELECT 1, which is Ediz's rule
    for failed requests and always counts as wrong. Returns how many lines were filled."""
    with open(pred_path, encoding="utf-8") as f:
        preds = f.read().split("\n")
    if preds and preds[-1] == "":
        preds.pop()
    if len(preds) != expected:
        sys.exit(f"ERROR: {pred_path} has {len(preds)} lines for {expected} questions.")
    empty = sum(1 for p in preds if not p.strip())
    with open(pred_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(p if p.strip() else "SELECT 1" for p in preds) + "\n")
    return empty


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def git_state():
    try:
        commit = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"], text=True).strip()
        dirty = bool(subprocess.check_output(["git", "-C", REPO, "status", "--porcelain"], text=True).strip())
        return {"commit": commit, "uncommitted_changes": dirty}
    except Exception as e:
        return {"error": str(e)}


def machine_info():
    info = {"platform": platform.platform(), "python": platform.python_version(),
            "cpu": platform.processor(), "logical_cpus": os.cpu_count()}
    if sys.platform == "win32":
        try:
            import winreg
            key = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as k:
                info["cpu"] = winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()

            class MemoryStatus(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + \
                           [(n, ctypes.c_ulonglong) for n in ("total", "avail", "total_page", "avail_page",
                                                              "total_virtual", "avail_virtual", "avail_ext")]
            m = MemoryStatus()
            m.dwLength = ctypes.sizeof(m)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            info["ram_bytes"] = m.total
        except Exception:
            pass
    elif sys.platform == "darwin":
        for key, cmd in [("cpu", ["sysctl", "-n", "machdep.cpu.brand_string"]),
                         ("ram_bytes", ["sysctl", "-n", "hw.memsize"])]:
            try:
                info[key] = subprocess.check_output(cmd, text=True).strip()
            except Exception:
                pass
    return info


def ollama_state(model):
    """Ollama version, the model's digest and quantization, and where it runs (CPU/GPU)."""
    state = {}
    try:
        state["version"] = requests.get(f"{OLLAMA}/api/version", timeout=5).json().get("version")
        for m in requests.get(f"{OLLAMA}/api/tags", timeout=5).json().get("models", []):
            if model in (m.get("name"), m.get("model")):
                state["model_digest"] = m.get("digest")
                state["model_details"] = m.get("details")
        for m in requests.get(f"{OLLAMA}/api/ps", timeout=5).json().get("models", []):
            if model in (m.get("name"), m.get("model")):
                size, vram = m.get("size") or 0, m.get("size_vram") or 0
                state["loaded_size_bytes"] = size
                state["processor"] = "100% CPU" if not vram else f"{100 * vram / size:.0f}% GPU"
                state["context_length"] = m.get("context_length")
    except Exception as e:
        state["error"] = str(e)
    return state


def check_ollama(model):
    try:
        tags = requests.get(f"{OLLAMA}/api/tags", timeout=5).json()
    except Exception as e:
        sys.exit(f"ERROR: cannot reach Ollama at {OLLAMA} ({e}). Start the Ollama app first.")
    names = {m.get("name") for m in tags.get("models", [])} | {m.get("model") for m in tags.get("models", [])}
    if model not in names:
        sys.exit(f"ERROR: model '{model}' is not pulled. Run:  ollama pull {model}\n"
                 f"Pulled models: {sorted(n for n in names if n)}")


def warm_up(real_post, url, body):
    """Loads the model with the script's own options (num_ctx etc.), so the first question's
    time does not include loading it. A different num_ctx would make Ollama reload the model."""
    options = dict(body.get("options") or {}, num_predict=1)
    real_post(url, timeout=600, json={"model": body["model"], "prompt": "SELECT 1", "stream": False, "options": options})


def fake_response(row, url):
    """Rebuilds the response of a logged request, so a resumed run replays it unchanged."""
    if row.get("exception") == "ReadTimeout":
        raise requests.exceptions.ReadTimeout(f"(replayed from log) {row.get('error', '')}")
    if row.get("exception"):
        raise requests.exceptions.RequestException(f"(replayed from log) {row['exception']}: {row.get('error', '')}")
    resp = requests.models.Response()
    resp.status_code = row["status"]
    resp.url = url
    resp.encoding = "utf-8"
    body = {"response": row.get("response", "")} if row["status"] == 200 else {"error": row.get("error", "")}
    resp._content = json.dumps(body).encode("utf-8")
    return resp


def summarize(rows):
    ok = [r for r in rows if r.get("status") == 200]
    walls = sorted(r["wall_s"] for r in ok)

    def pct(q):
        return round(statistics.quantiles(walls, n=100)[q - 1], 2) if len(walls) > 1 else (walls or [None])[0]

    def rate(count_key, dur_key):
        rates = [r[count_key] / r[dur_key] for r in ok if r.get(dur_key)]
        return round(statistics.mean(rates), 1) if rates else None

    return {
        "questions": len(rows),
        "failed_requests": len(rows) - len(ok),
        "failed_breakdown": {k: sum(1 for r in rows if (r.get("exception") or f"HTTP{r.get('status')}") == k)
                             for k in sorted({r.get("exception") or f"HTTP{r.get('status')}"
                                              for r in rows if r.get("status") != 200})},
        "replayed_from_log": sum(1 for r in rows if r.get("replayed")),
        "model_minutes_total": round(sum(r.get("wall_s", 0) for r in rows) / 60, 1),
        "latency_wall_s": {"mean": round(statistics.mean(walls), 2) if walls else None,
                           "p50": round(statistics.median(walls), 2) if walls else None,
                           "p95": pct(95), "max": walls[-1] if walls else None},
        "prompt_tokens_mean": round(statistics.mean(r.get("prompt_eval_count", 0) for r in ok), 1) if ok else None,
        "gen_tokens_mean": round(statistics.mean(r.get("eval_count", 0) for r in ok), 1) if ok else None,
        "prompt_tokens_per_s_mean": rate("prompt_eval_count", "prompt_eval_duration"),
        "gen_tokens_per_s_mean": rate("eval_count", "eval_duration"),
        "stopped_by_length_limit": sum(1 for r in ok if r.get("done_reason") == "length"),
    }


def main():
    ap = argparse.ArgumentParser(description="Run Ediz's Spider scripts with another Ollama model.")
    ap.add_argument("--model", required=True, help="Ollama model name, e.g. qwen2.5-coder:1.5b")
    ap.add_argument("--variant", required=True, choices=SCRIPTS)
    ap.add_argument("--scripts_dir", default=EDIZ_DIR, help="folder with Ediz's scripts (default: his folder in this repo)")
    ap.add_argument("--work_dir", default=HERE, help="folder that holds data/ (the scripts use relative paths)")
    ap.add_argument("--out_dir", default=os.path.join(HERE, "results_basil"))
    ap.add_argument("--limit", type=int, help="stop after N questions (smoke test; no prediction file is written)")
    args = ap.parse_args()

    script_name, default_output = SCRIPTS[args.variant]
    script_path = os.path.join(args.scripts_dir, script_name)
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    tag = args.model.replace(":", "-").replace("/", "-")
    raw_path = os.path.join(out_dir, f"raw_{args.variant}_{tag}.jsonl")

    check_ollama(args.model)
    previous = []
    if os.path.exists(raw_path):
        with open(raw_path, encoding="utf-8") as f:
            previous = [json.loads(line) for line in f if line.strip()]
        print(f"Resuming: {len(previous)} answered questions found in {raw_path}")

    real_post = requests.post
    rows = []
    warmed = []
    log = open(raw_path, "a", encoding="utf-8")

    def patched_post(url, *a, **kw):
        url = url.replace("://localhost:", "://127.0.0.1:")  # same server, without the 2 s IPv6 detour (see OLLAMA)
        body = kw.get("json")
        if not (isinstance(body, dict) and "model" in body):
            return real_post(url, *a, **kw)
        if args.limit is not None and len(rows) >= args.limit:
            raise StopRun()
        kw["json"] = body = dict(body, model=args.model)
        n = len(rows)
        prompt_sha = hashlib.sha256(body.get("prompt", "").encode("utf-8")).hexdigest()[:16]
        db = re.search(r"Database name: (\S+)", body.get("prompt", ""))

        if n < len(previous):
            row = previous[n]
            if row["prompt_sha"] != prompt_sha:
                sys.exit(f"ERROR: question {n} in {raw_path} has a different prompt. "
                         f"The log is from another setup; move it away to start fresh.")
            rows.append(dict(row, replayed=True))
            return fake_response(row, url)

        if not warmed:
            warm_up(real_post, url, body)
            warmed.append(True)
        row = {"n": n, "db_id": db.group(1) if db else None, "prompt_sha": prompt_sha}
        t0 = time.perf_counter()
        try:
            resp = real_post(url, *a, **kw)
        except Exception as e:
            row.update(wall_s=round(time.perf_counter() - t0, 3), status=None,
                       exception=type(e).__name__, error=str(e)[:300])
            rows.append(row)
            log.write(json.dumps(row) + "\n")
            log.flush()
            raise
        row.update(wall_s=round(time.perf_counter() - t0, 3), status=resp.status_code)
        if resp.status_code == 404:
            log.close()
            print(f"\nERROR: Ollama returned 404 (model not found): {resp.text[:300]}\nRun stopped.")
            os._exit(1)
        try:
            data = resp.json()
        except ValueError:
            data = {}
        if resp.status_code == 200:
            row["response"] = data.get("response", "")
            for k in TIMING_FIELDS:
                if k in data:
                    row[k] = round(data[k] / 1e9, 3) if k.endswith("duration") else data[k]
        else:
            row["error"] = (data.get("error") or resp.text)[:300]
        rows.append(row)
        log.write(json.dumps(row, ensure_ascii=False) + "\n")
        log.flush()
        return resp

    requests.post = patched_post
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    t_start = time.perf_counter()
    os.chdir(args.work_dir)
    partial = False
    try:
        runpy.run_path(script_path, run_name="__main__")
    except StopRun:
        partial = True
        print(f"\nStopped after {len(rows)} questions (--limit).")
    finally:
        requests.post = real_post
        log.close()
    elapsed = time.perf_counter() - t_start

    out_pred, empty_filled = None, None
    if not partial:
        out_pred = os.path.join(out_dir, f"predict_{args.variant}_{tag}.sql")
        os.replace(default_output, out_pred)
        empty_filled = fill_empty_lines(out_pred, expected=len(rows))

    if rows:
        keys = ["n", "db_id", "status", "exception", "wall_s"] + [k for k in TIMING_FIELDS] + ["replayed"]
        csv_name = f"timings_{args.variant}_{tag}{'_partial' if partial else ''}.csv"
        with open(os.path.join(out_dir, csv_name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    summary = {
        "benchmark": BENCHMARK,
        "model": args.model,
        "variant": args.variant,
        "script": os.path.relpath(script_path, REPO).replace("\\", "/"),
        "script_sha256": sha256_file(script_path),
        "git": git_state(),
        "started": started,
        "finished": time.strftime("%Y-%m-%d %H:%M:%S"),
        "partial_run": partial,
        "minutes_this_invocation": round(elapsed / 60, 1),
        **summarize(rows),
        "empty_answers_written_as_select_1": empty_filled,
        "machine": machine_info(),
        "ollama": ollama_state(args.model),
        "predictions_file": os.path.relpath(out_pred, REPO).replace("\\", "/") if out_pred else None,
        "raw_log": os.path.relpath(raw_path, REPO).replace("\\", "/"),
    }
    name = f"summary_{args.variant}_{tag}{'_partial' if partial else ''}.json"
    with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
