"""Patches the TRELLIS.2 RunPod worker's /app/handler.py in place, then the worker is started as usual.

Why: the stock handler (WeAreBraveLabs/trellis2-runpod) fixes the face count by resolution (512: 100k, 1024: 500k, 1536: 1M) and does not
accept it as an input. At 1024+ the GLB is ~15 MB (~21 MB as base64), above RunPod's output limits (/run 10 MB, /runsync 20 MB). RunPod then
answers 400 to the worker's result upload, the job still shows COMPLETED, and the model is lost.

What it changes (3 small edits, each anchored on an exact line; it stops with an error if an anchor is missing, and is idempotent):
  1. optional input `decimation_target` (face count) overriding the per-resolution default;
  2. optional input `max_output_mb` (default 9.5, base64 size): a too-large result now FAILS the job with a clear message instead of vanishing;
  3. nothing else: default behaviour with no new inputs is unchanged.
Usage in the endpoint's container start command:
  python3 -c "import urllib.request as u;exec(u.urlopen('<raw url of this file at a pinned commit>').read())" && python3 -u /app/handler.py
or: python3 patch_handler.py /app/handler.py
"""
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "/app/handler.py"
MARK = "# patched by patch_handler.py"

EDITS = [
    ("    decimation_target = decimation_targets.get(resolution, 500000)\n",
     "    decimation_target = decimation_targets.get(resolution, 500000)\n"
     "    if job_input.get(\"decimation_target\"):   " + MARK + "\n"
     "        decimation_target = int(job_input[\"decimation_target\"])\n"
     "    max_output_mb = float(job_input.get(\"max_output_mb\", 9.5))\n"),
    ("    model_size_mb = len(model_base64) * 3 / 4 / 1024 / 1024\n",
     "    model_size_mb = len(model_base64) * 3 / 4 / 1024 / 1024\n"
     "    if len(model_base64) / 1024 / 1024 > max_output_mb:   " + MARK + "\n"
     "        return {\"error\": \"Result too large: %.1f MB base64 > max_output_mb=%s. Lower decimation_target (now %d); about 33 bytes per face.\" % (len(model_base64) / 1024 / 1024, max_output_mb, decimation_target)}\n"),
]

src = open(PATH, encoding="utf-8").read()
if MARK in src:
    print("already patched:", PATH)
else:
    for old, new in EDITS:
        if src.count(old) != 1:
            sys.exit("patch_handler: anchor not found exactly once (the worker code changed?): " + old.strip())
        src = src.replace(old, new, 1)
    open(PATH, "w", encoding="utf-8").write(src)
    print("patched:", PATH)
