#!/usr/bin/env python3
"""Dispara um render no endpoint RunPods e faz polling até terminar.
Uso: python rp_run.py <sermon> [frames]   ex: python rp_run.py 1 0-150"""
import os, sys, json, time, urllib.request, urllib.error

ENDPOINT = "kfvaheum0qzuiv"


def load_env(path):
    env = {}
    for raw in open(path, encoding="utf-8"):
        line = raw.replace("\r", "").strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v
    return env


def api(method, url, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def main():
    sermon = sys.argv[1] if len(sys.argv) > 1 else "1"
    frames = sys.argv[2] if len(sys.argv) > 2 else None
    env = load_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
    token = env["RUNPOD_API_KEY"]

    inp = {"sermon": int(sermon)}
    if frames:
        inp["frames"] = frames
    conc = os.environ.get("CONCURRENCY")
    if conc:
        inp["concurrency"] = int(conc)

    print(f"▶ disparando: {inp}")
    st, res = api("POST", f"https://api.runpod.ai/v2/{ENDPOINT}/run", token, {"input": inp})
    if st != 200 or "id" not in res:
        sys.exit(f"❌ falha ao disparar {st}: {json.dumps(res)[:400]}")
    job_id = res["id"]
    print(f"  job_id = {job_id}  (status inicial: {res.get('status')})")

    start = time.time()
    last = None
    while True:
        time.sleep(15)
        st, s = api("GET", f"https://api.runpod.ai/v2/{ENDPOINT}/status/{job_id}", token)
        status = s.get("status", "?")
        elapsed = int(time.time() - start)
        if status != last:
            print(f"  [{elapsed}s] {status}")
            last = status
        if status in ("COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"):
            print(json.dumps(s, indent=2)[:1500])
            break
        if elapsed > 3000:
            print("  ⏱️ timeout do monitor (50min) — checar no painel")
            break


if __name__ == "__main__":
    main()
