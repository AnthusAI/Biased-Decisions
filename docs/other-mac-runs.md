# Running Kev collection on another Mac

## What a run is, and the one-job rule

A run is one Kanbus issue from epic BD-996e20: a specific task's still-missing cells for the Kev model, resumable across interruptions, with answer files written to `answers/kev/<task>/`. A cell is answered exactly once; completed cells are not re-requested.

Only one heavy job at a time on the machine. The Kev server holds the GPU and about 4 GiB of memory, and other heavy work (another run, Laya, a full test suite) slows it and causes timeouts. Stop other heavy jobs before starting.

## One-time setup on a fresh Mac

Apple silicon is required.

Clone the repository and check out main:

```sh
git clone https://github.com/AnthusAI/Biased-Decisions.git
```

```sh
cd Biased-Decisions && git checkout main && git pull
```

Create a Python 3.12.2 virtual environment from the Kev requirements. The exact Python version matters:

```sh
python3.12 -m venv var/kev-venv
```

```sh
var/kev-venv/bin/python -m pip install --no-cache-dir -r studies/kev/requirements.txt
```

Activate the virtual environment for the rest of the setup and all runs:

```sh
source var/kev-venv/bin/activate
```

Install the repository's own package (a run needs only its light dependencies, not the test or build extras):

```sh
pip install -e .
```

Get the two pinned model snapshots into the cache (about 1.7 GB). The launcher runs offline, so download them first. Either download them:

```sh
HF_HOME="${KEV_HF_HOME:-$PWD/var/hf-cache}" python -c "from huggingface_hub import snapshot_download as d; d('jaredpalmer/kev-0.8b', revision='54f4f8777356cd5bbbb6c6919c657f26e6f2f6d8'); d('Qwen/Qwen3.5-0.8B-Base', revision='dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68')"
```

or copy the first Mac's cache folder (`var/hf-cache`, wherever it lives there) to this Mac's `var/hf-cache` with `rsync -a`. Check that both snapshot folders exist:

```sh
ls var/hf-cache/hub/models--jaredpalmer--kev-0.8b/snapshots var/hf-cache/hub/models--Qwen--Qwen3.5-0.8B-Base/snapshots
```

The first folder must show `54f4f8777356cd5bbbb6c6919c657f26e6f2f6d8` and the second `dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68`.

## Doing a run from the issue

Read your run issue first (`kbs show <issue-id>`). It names the task; the manifest is `docs/kev-runs/<task>.json`. Pull main first, because the manifests and the runner's item cap are committed there.

Within your repository, start the Kev server in a dedicated terminal:

```sh
python scripts/start_kev_server.py
```

Wait until the server responds at http://127.0.0.1:8009:

```sh
curl http://127.0.0.1:8009/v1/models
```

The server will print `{"data": [...]}` when ready. This can take 30 seconds to a few minutes on first launch while the model loads.

In another terminal (with the venv activated), run the collect command exactly as specified in the issue. The issue task name and manifest path are pinned. For example:

```sh
KEV_BASE_URL=http://127.0.0.1:8009 python -m scripts.run_kev_study collect \
  --model kev-latest \
  --server-revision c9c1f855505336ac32092a5f68305d397f7fcc3e \
  --base-revision dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68 \
  --backend mlx --dtype bfloat16 --calibration 2.406050072164233 \
  --manifest docs/kev-runs/<task>.json
```

The command resumes if interrupted. It will not re-request answered cells or redraw inputs based on answers. When it completes, it prints `{"mode": "collect", ...}` with `"complete": true`.

Stop the server after collection finishes:

```sh
# In the server terminal: Ctrl+C to stop
```

## Returning the data

Create a new branch for this run, named after the issue ID:

```sh
git checkout -b runs/<issue-id>
```

Add only the finished answer files from this run:

```sh
git add answers/kev/<task>/*.jsonl.gz answers/kev/<task>/*.metadata.json
```

Never add partial files (`*.partial.jsonl`), cached data, or model weights.

Commit the answers:

```sh
git commit -m "Kev answers for <task> from <issue-id>"
```

Push the branch (never main):

```sh
git push origin runs/<issue-id>
```

Comment on the original Kanbus issue with:
- Request count from the manifest (found in the issue or `docs/kev-runs/<task>.json`)
- Any errors or issues encountered during collection

Close the issue.

Do not run `bd replay`, do not edit `studies/`, do not merge the branch. The steering team will review and merge when ready.

## If it goes wrong

**Server will not start:** Check that the MLX build is installed and the model weights are in the cache. Verify `ls var/hf-cache/hub/` shows model directories. If the port is in use, check for stray `kev.serve` processes: `ps aux | grep kev`.

**Out of disk space:** Check `df -h`. The model cache and intermediate data can use significant space. Free space if needed, then resume the collect command (it will skip completed items).

**Machine too loaded:** Stop other work. Check `top` for CPU and memory usage. High memory or swap usage will slow inference and cause timeouts. Never run two Kev jobs or a Kev job with Laya or live replay simultaneously.

**Interrupted run:** Simply run the collect command again. It resumes from the last completed item and will not re-request answered cells.

## Not yet verified

This guide has not yet been followed end to end on a second Mac. If a step is wrong, fix this file in the same branch and say so in the issue comment.
