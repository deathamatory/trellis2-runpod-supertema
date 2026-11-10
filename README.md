# trellis2-runpod-supertema

A tiny patch for the RunPod TRELLIS.2 worker image `wearebravelabs/trellis2-runpod`, without rebuilding the image.

`patch_handler.py` edits `/app/handler.py` when the worker starts:
- new optional input `decimation_target` (face count) so resolution 1024/1536 results can be made small enough for RunPod's output limits (`/run` 10 MB, `/runsync` 20 MB);
- new optional input `max_output_mb` (default 9.5): an oversized result fails the job with a clear error instead of being silently lost.

Without the new inputs the worker behaves exactly as before. Nothing from the original repository is copied here.

Endpoint container start command (pin the commit):

    python3 -c "import urllib.request as u;exec(u.urlopen('https://raw.githubusercontent.com/deathamatory/trellis2-runpod-supertema/<commit>/patch_handler.py').read())" && python3 -u /app/handler.py
