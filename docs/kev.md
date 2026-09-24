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

Each answer is flushed to a partial JSONL file. A sidecar manifest fingerprints the task text,
question wording, option order, model identity and run provenance. Resume refuses changed inputs,
model identity, or provenance. Completed records are written atomically to
`answers/kev/<task>/<cue>.jsonl.gz`; a completed rerun sends no requests. Keep the sidecar with
the answer record as part of its provenance.

Choice probabilities must cover each requested option and sum to one within the four-decimal
rounding tolerance used by Kev's API. The adapter specifications use fake HTTP responses and
verify request shape, option ordering, fresh repeated requests, answer coverage and probability validation. They do not download weights
or verify hardware support. Hardware and checkpoint behavior must be established by the pinned
runtime and recorded study run.
