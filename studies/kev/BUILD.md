# Kev build and collection notes

Study registration: `docs/kev-preregistration.md`, committed in `a5a6049`
before any Kev inference. Frozen inputs: `docs/kev-coverage.json`.

## Identity

| Setting | Value |
| --- | --- |
| Checkpoint | `jaredpalmer/kev-0.8b@54f4f8777356cd5bbbb6c6919c657f26e6f2f6d8` |
| Base | `Qwen/Qwen3.5-0.8B-Base@dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68` |
| Server source | `https://github.com/jaredpalmer/kev`, commit `c9c1f855505336ac32092a5f68305d397f7fcc3e` |
| Python | 3.12.2 |
| Intended backend | MLX, bfloat16 backbone and upstream fp32 pointer head |
| Checkpoint temperature | `2.406050072164233` (read from pinned `head.pt` on CPU) |
| Prefix cache | disabled |
| Date-fact augmentation | disabled |
| LoRA interpolation | 1, unchanged |
| API request alias | `kev-latest`; immutable identity comes from the pinned server run |
| Machine | Apple silicon MacBookPro18,4; 32 GiB RAM |

`requirements.txt` records the isolated runtime's exact installed dependencies.
The source and weight downloads do not perform inference. No shared Python
environment was changed. The application receives plain biography text and the
committed question and ordered options. The server's deployment alias is not used
as evidence of checkpoint identity.

## Resource policy

Wait for the existing Laya GPU job to finish and check for another active inference
job before starting Kev. Use one request at a time. Set the MLX allocation guideline
to 4 GiB, the free-cache limit to 256 MiB, and the process's wired-memory limit to
4 GiB before loading the checkpoint. These limits do not bound all Python/PyTorch
memory; observe process memory and system pressure as well. Stop on resource
pressure and retain the partial record.

The first 20 committed original surgeon/physician bios form the timing pilot.
They stay in the normal gender-pronouns record; no selection depends on answers.
After checking the pilot's timing and memory, resume the same full cell. Do not run
a site build or full replay concurrently with the model server.

## Setup

The runtime can be recreated separately from the harness:

```sh
python3.12 -m venv var/kev-venv
var/kev-venv/bin/python -m pip install --no-cache-dir -r studies/kev/requirements.txt
```

Use a dedicated Hugging Face cache for the pinned checkpoint and base. Start the
standard `kev.serve` module with `--run` set to the complete checkpoint identity
above and a local-only port. Set `KEV_BACKEND=mlx`, `KEV_DTYPE=bf16`,
`KEV_PREFIX_CACHE=0`, `KEV_DATE_FACTS=0`, and leave temperature at the stored value.
Verify `/v1/models` before collection. The collector's exact commands are documented
in `docs/kev.md`; its run manifests bind results to inputs and runtime identity.

## Status and elapsed time

Runtime and weights prepared. Collection and timing pending exclusive GPU access.
No hosted inference has been purchased.
