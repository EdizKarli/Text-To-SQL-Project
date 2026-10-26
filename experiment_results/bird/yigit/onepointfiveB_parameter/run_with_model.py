"""
run_with_model.py — Ediz'in BIRD mini-dev script'lerini başka bir modelle,
prompt'lara ve mantığa HİÇ dokunmadan çalıştırır; ek olarak her soru için
süre ve token istatistiklerini kaydeder.

Nasıl çalışır:
  - Ediz'in script'i Ollama'ya istek attığında, model adı bizim verdiğimizle değiştirilir.
  - Ollama'nın her cevapta döndürdüğü süre bilgileri (total_duration, eval_count vb.) kaydedilir.
  - Script bitince çıktı dosyası model adıyla yeniden adlandırılır, özet ve CSV yazılır.

Kullanım (data/ ve mini_dev_data/ klasörlerinin olduğu klasörden):
  python run_with_model.py --model qwen2.5-coder:1.5b --variant schema

Varyantlar: noschema | schema | pruned_v1 | pruned_v2
"""
import argparse
import csv
import json
import os
import platform
import runpy
import statistics
import subprocess
import sys
import time

import requests

SCRIPTS = {
    "noschema": ("bird_infer.py", "predict_mini_dev.txt"),
    "schema": ("bird_infer_schema.py", "predict_mini_dev_schema.json"),
    "pruned_v1": ("bird_infer_pruned.py", "predict_mini_dev_pruned.json"),
    "pruned_v2": ("bird_infer_pruned_vol2.py", "predict_mini_dev_pruned_v2.json"),
}


def machine_info():
    info = {"platform": platform.platform(), "python": platform.python_version()}
    if sys.platform == "darwin":
        for key, cmd in [("cpu", ["sysctl", "-n", "machdep.cpu.brand_string"]),
                         ("ram_bytes", ["sysctl", "-n", "hw.memsize"])]:
            try:
                info[key] = subprocess.check_output(cmd, text=True).strip()
            except Exception:
                pass
    else:
        info["cpu"] = platform.processor()
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="Ollama model adı, ör. qwen2.5-coder:1.5b")
    ap.add_argument("--variant", required=True, choices=SCRIPTS.keys())
    ap.add_argument("--scripts_dir", default=".", help="Ediz'in .py dosyalarının olduğu klasör")
    ap.add_argument("--out_dir", default="results_yigit")
    ap.add_argument("--limit", type=int, default=0,
                    help="Sadece hız ölçümü: ilk N sorudan sonra dur (tahmin dosyası yazılmaz)")
    args = ap.parse_args()

    script_name, default_output = SCRIPTS[args.variant]
    script_path = os.path.join(args.scripts_dir, script_name)
    os.makedirs(args.out_dir, exist_ok=True)
    tag = args.model.replace(":", "-").replace("/", "-")

    # Ön kontrol: Ollama açık mı ve model indirilmiş mi? (yoksa 500 soru boşuna 404 alır)
    try:
        tags = requests.get("http://localhost:11434/api/tags", timeout=5).json()
    except Exception as e:
        sys.exit(f"HATA: Ollama'ya bağlanılamadı ({e}). Ollama uygulamasını aç.")
    names = {m.get("name") for m in tags.get("models", [])} | {m.get("model") for m in tags.get("models", [])}
    if args.model not in names:
        sys.exit(f"HATA: '{args.model}' modeli yüklü değil. Önce çalıştır:  ollama pull {args.model}\n"
                 f"Yüklü modeller: {sorted(n for n in names if n)}")

    timings = []
    real_post = requests.post

    if args.limit:
        # Modeli önceden belleğe yükle, böylece yükleme süresi ölçüme girmez
        real_post("http://localhost:11434/api/generate",
                  json={"model": args.model, "prompt": "hi", "stream": False}, timeout=300)

    def finish_latency_run():
        tag_ = args.model.replace(":", "-").replace("/", "-")
        lat_dir = os.path.join(args.out_dir, "latency")
        os.makedirs(lat_dir, exist_ok=True)
        keys = sorted({k for r in timings for k in r})
        with open(os.path.join(lat_dir, f"timings_{args.variant}_{tag_}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(timings)
        ok = sorted(r["wall_s"] for r in timings if not r.get("error")) or [0]
        rates = [r["gen_tokens"] / r["gen_s"] for r in timings if r.get("gen_s")]
        try:
            ps = subprocess.check_output(["ollama", "ps"], text=True)
        except Exception as e:
            ps = f"(ollama ps çalışmadı: {e})"
        s = {
            "model": args.model, "variant": args.variant, "questions": len(timings),
            "failed_requests": sum(1 for r in timings if r.get("error")),
            "latency_mean_s": round(statistics.mean(ok), 2),
            "latency_p50_s": round(ok[len(ok) // 2], 2),
            "latency_p95_s": round(ok[int(len(ok) * 0.95) - 1], 2) if len(ok) > 1 else ok[0],
            "gen_tokens_per_s_mean": round(statistics.mean(rates), 1) if rates else None,
            "ollama_ps_at_end": ps,
        }
        with open(os.path.join(lat_dir, f"summary_{args.variant}_{tag_}.json"), "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2, ensure_ascii=False)
        print(json.dumps(s, indent=2, ensure_ascii=False))
        os._exit(0)

    def patched_post(url, *a, **kw):
        if "json" in kw and isinstance(kw["json"], dict) and "model" in kw["json"]:
            kw["json"] = dict(kw["json"], model=args.model)
        t0 = time.perf_counter()
        try:
            resp = real_post(url, *a, **kw)
        except Exception as e:
            # Zaman aşımı vb.: kaydet, Ediz'in script'i kendi kuralıyla ("SELECT 1") devam etsin
            timings.append({"wall_s": round(time.perf_counter() - t0, 3), "error": type(e).__name__})
            raise
        wall = time.perf_counter() - t0
        if resp.status_code == 404:
            # Sadece "model yok" durumunda dur; diğer hatalar (ör. 500 token repeat) tek soruluk hatadır
            print(f"\nHATA: Ollama 404 döndürdü (model bulunamadı): {resp.text[:300]}\nÇalıştırma durduruldu.")
            os._exit(1)
        row = {"wall_s": round(wall, 3)}
        if resp.status_code != 200:
            row["error"] = f"HTTP{resp.status_code}: {resp.text[:80]}"
        try:
            body = resp.json()
            ns = 1e9
            row.update({
                "total_s": round(body.get("total_duration", 0) / ns, 3),
                "load_s": round(body.get("load_duration", 0) / ns, 3),
                "prompt_tokens": body.get("prompt_eval_count", 0),
                "prompt_s": round(body.get("prompt_eval_duration", 0) / ns, 3),
                "gen_tokens": body.get("eval_count", 0),
                "gen_s": round(body.get("eval_duration", 0) / ns, 3),
            })
        except Exception:
            pass
        timings.append(row)
        if args.limit and len(timings) >= args.limit:
            finish_latency_run()
        return resp

    requests.post = patched_post
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    t_start = time.perf_counter()
    runpy.run_path(script_path, run_name="__main__")
    elapsed = time.perf_counter() - t_start

    # Çıktıyı model adıyla kaydet (noschema varyantı .txt yazıyor; diğerleriyle aynı JSON biçimine çeviriyoruz)
    if args.variant == "noschema":
        with open("data/mini_dev_sqlite.json", encoding="utf-8") as f:
            content = f.read().strip()
        data = json.loads(content) if content.startswith("[") else [json.loads(l) for l in content.splitlines() if l.strip()]
        with open(default_output, encoding="utf-8") as f:
            lines = [l.rstrip("\n") for l in f if l.strip()]
        preds = {str(item.get("question_id", i)): line for i, (item, line) in enumerate(zip(data, lines))}
        out_pred = os.path.join(args.out_dir, f"predict_{args.variant}_{tag}.json")
        with open(out_pred, "w", encoding="utf-8") as f:
            json.dump(preds, f, indent=2)
    else:
        out_pred = os.path.join(args.out_dir, f"predict_{args.variant}_{tag}.json")
        os.replace(default_output, out_pred)

    # Süre CSV'si
    csv_path = os.path.join(args.out_dir, f"timings_{args.variant}_{tag}.csv")
    if timings:
        keys = sorted({k for r in timings for k in r})
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(timings)

    walls = sorted(r["wall_s"] for r in timings if not r.get("error")) or [0]
    gen_rates = [r["gen_tokens"] / r["gen_s"] for r in timings if r.get("gen_s")]
    try:
        ollama_ps = subprocess.check_output(["ollama", "ps"], text=True)
    except Exception as e:
        ollama_ps = f"(ollama ps çalışmadı: {e})"

    summary = {
        "model": args.model,
        "variant": args.variant,
        "script": script_name,
        "started": started,
        "questions": len(timings),
        "failed_requests": sum(1 for r in timings if r.get("error")),
        "failed_breakdown": {k: sum(1 for r in timings if r.get("error", "").startswith(k)) for k in ("ReadTimeout", "HTTP500")},
        "total_minutes": round(elapsed / 60, 1),
        "latency_mean_s": round(statistics.mean(walls), 2),
        "latency_p50_s": round(walls[len(walls) // 2], 2),
        "latency_p95_s": round(walls[int(len(walls) * 0.95) - 1], 2) if len(walls) > 1 else walls[0],
        "gen_tokens_per_s_mean": round(statistics.mean(gen_rates), 1) if gen_rates else None,
        "machine": machine_info(),
        "ollama_ps_at_end": ollama_ps,
        "predictions_file": out_pred,
    }
    with open(os.path.join(args.out_dir, f"summary_{args.variant}_{tag}.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
