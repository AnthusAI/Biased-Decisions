# Kev engine adapter

The Kev adapter sends the task text and ordered question definitions to an explicitly configured
Kev server at `KEV_BASE_URL/v1/systemone`. It uses the standard library for HTTP, so importing
the project does not install or load model code. An optional bearer credential comes only from
`KEV_API_KEY`; the adapter never uses Jev's endpoint or credentials. Requests have no answer
cache, so repeated inputs are separate model calls.

Start a Kev server using the official [Kev serving instructions](https://github.com/jaredpalmer/kev).
Set `KEV_BASE_URL` to that server's base URL (for example, a local loopback URL) and, when the
server requires authentication, set `KEV_API_KEY` in the process environment. The `KEV_MODEL`
setting selects the server model name and defaults to `kev-latest`. A deployment alias is not an
immutable checkpoint identity.

Preview a cell without contacting the server:

```sh
python -m scripts.collect_task kev surgeon-physician gender-pronouns --dry-run
```

The collector reads committed task version files. It also supports the repository's explicit
multi-question `questions:` task format for Noul questions, preserving each question key and
instruction as supplied. Unknown formats and missing cue files are refused instead of being
rebuilt during collection. A bounded pilot can stop after a fixed number of new items while
leaving the full cell resumable with `--max-new-items 20`.

For actual collection, supply the pinned runtime identity selected for the study. The server's
`GET /v1/models` response must expose the selected model and immutable run/checkpoint identity.
The server revision is supplied explicitly because that endpoint does not report it:

```sh
python -m scripts.collect_task kev surgeon-physician gender-pronouns \
  --server-revision <40-hex-server-revision> --base-revision <40-hex-base-revision> \
  --backend <backend> --dtype <dtype> \
  --calibration <calibration-identity>
```

Each answer is flushed to a partial JSONL file. A sidecar manifest fingerprints complete selected items, task definitions,
question wording, option order, model identity and run provenance. Resume refuses changed inputs,
model identity, or provenance. Completed records are written atomically to
`answers/kev/<task>/<cue>.jsonl.gz`; a completed rerun sends no requests. Keep the sidecar with
the answer record as part of its provenance.

Choice probabilities must cover each requested option and sum to one within the four-decimal
rounding tolerance used by Kev's API. The adapter specifications use fake HTTP responses and
verify request shape, option ordering, fresh repeated requests, answer coverage and probability
validation. A real 20-item pilot has since verified the pinned checkpoint over HTTP on Apple
silicon with MLX and bfloat16; its predictions, identity and timings are in the [study build
notes](../studies/kev/BUILD.md) and [pilot metadata](../studies/kev/pilot.metadata.json). This
verifies inference only under that setup. CPU and CUDA inference have not been verified here. The
HTTP adapter itself has no backend dependency and can communicate with a Kev server on other
hardware.

## Run the registered study

Validate every frozen input hash and planned cell count without network access:

```sh
python -m scripts.run_kev_study dry-run
```

After the pinned local server is running and the machine is reserved for this job,
run the retained timing pilot with the registered identity:

```sh
KEV_BASE_URL=http://127.0.0.1:8009 python -m scripts.run_kev_study pilot \
  --model kev-latest \
  --server-revision c9c1f855505336ac32092a5f68305d397f7fcc3e \
  --base-revision dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68 \
  --backend mlx --dtype bfloat16 --calibration 2.406050072164233
```

The pilot retains the first 20 original surgeon/physician bios in
`studies/kev/pilot.jsonl`, with immutable metadata and timing alongside it. The
normal gender record interleaves originals and twins, so normal collection makes
those 20 calls again in its unchanged order. A completed pilot rerun sends no
requests; an interrupted pilot resumes its saved prefix.

After reviewing timing and available resources, use the same command with
`collect` in place of `pilot` to collect every registered cell. The runner checks
all file hashes and counts before creating the client, then verifies that the
server checkpoint exactly matches the manifest. It maps the study's `option-order`
contrast to the collector's `option-order-reversed` answer file. It never rebuilds
inputs or drops items based on their answers.

Incoming coverage belongs in a committed preregistration amendment and manifest
before collection. The existing collector can consume its shared definitions;
new scorer formats still require the corresponding shared scorer integration.
