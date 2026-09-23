# Engine coverage

Every engine in `docs/decision-models-survey.md`'s summary table, plus Jev, Laya, and the
`laya-mlx` port tracked as their own row because it ships
as a separate pip package with its own hardware story. "Apple silicon / CPU / CUDA" repeats what
the survey states for each engine, not what has been tried in this harness. "Status" is
`measured` (a committed record exists), `story open` (a Kanbus story tracks the adapter, not yet
run), or `not runnable here` (no documented path onto an Apple-silicon Mac or its CPU).

| Engine | Maker | Open / hosted | Licence | Option probabilities | Apple silicon / CPU / CUDA | pip package | Status | Kanbus story |
|---|---|---|---|---|---|---|---|---|
| Jev | TypeSafe AI | Hosted API | proprietary; SDK MIT | yes | n/a (API) | `typesafe-sdk` | measured | — |
| Kev | Jared Palmer | Open weights | Apache-2.0 | yes | Qwen3 ckpt: MPS bf16; Qwen3.5 ckpt: MPS fallback, slow, no MLX yet / CPU not stated / CUDA+ROCm yes | none (git + `uv sync`) | story open | [BD-dc51ca](../issues/BD-dc51ca9b-6149-495e-979f-22268681e251.json) |
| Laya | Convai Innovations | Open weights | Apache-2.0 | yes | CPU yes / CUDA yes / MPS not stated (see `laya-mlx`) | `laya` | measured | — |
| laya-mlx | mizorewww (port) | Open weights | Apache-2.0 | yes | Apple silicon only (MLX) | `laya-mlx` | story open | [BD-b3c876](../issues/BD-b3c8763a-d3ca-4553-a5fb-31d8cf65d29a.json) |
| Von | wfzyx | Open weights | Apache-2.0 | yes | MPS, CPU, CUDA, ROCm all listed | `von-sdk` | story open | [BD-4383fb](../issues/BD-4383fb6e-c187-46b0-8493-65452dde07b5.json) |
| System One Gemma | Akash Kamat | Open weights | code Apache-2.0; weights CC-BY-NC-4.0 | yes | CPU yes; MPS/MLX not stated | none (clone + requirements) | story open | [BD-a6f026](../issues/BD-a6f0268a-82ca-4017-9b8e-44a27dd9fde5.json) |
| Tiny-Jev | lostargon | Open weights | Apache-2.0 | yes | CUDA, MPS, CPU | none (`transformers`) | story open | [BD-5dadcd](../issues/BD-5dadcd25-19ca-434f-8ee1-1392bd38ad2b.json) |
| Decider | Mapika | Open weights | Apache-2.0 | yes | CUDA (bf16, FP8); MPS fp16 merged 2026-09-22; CPU bf16 | `decider-ai` | story open | [BD-2d6909](../issues/BD-2d6909ec-b530-412b-84e6-2fe2f0978fde.json) |
| this-that-model | FLock.io | Open weights | MIT (weights); base Apache-2.0 | yes | CUDA, CPU fp32, MPS fp16 | none (`pip install -e .`) | story open | [BD-bfec5e](../issues/BD-bfec5ea5-f4f4-4a1a-8c07-97ec1afa1cd0.json) |
| Bespoke-Nimble-9B | Bespoke Labs | Open weights (LoRA) | Apache-2.0 | yes | MLX backend on Mac; CUDA bf16; CPU "limited" | none (requirements files) | story open | [BD-45c200](../issues/BD-45c20012-a076-4841-90de-dda5219badec.json) |
| open-jev-deberta-v3-large | kotoba-lang | Open weights | Apache-2.0 | yes | CPU yes (M1 Max fp32); CUDA yes; MPS not stated | git install | story open | [BD-eff9fb](../issues/BD-eff9fba6-16f0-4fbf-b2c0-9b1c9f5aca4e.json) |
| Verdict / openJev-verdict-2.0 | heman10x | Open weights | Apache-2.0 | yes | CPU via ONNX Runtime, WebGPU, PyTorch server; MPS not stated | none (git install) | story open | [BD-431125](../issues/BD-431125d5-7275-4ffc-bafe-b13212a0dfe5.json) |
| jeff | logan-markewich | Open code; weights are Knowledgator GLiFormer | MIT (code) | yes | auto CUDA -> MPS -> CPU; ONNX int8 CPU option | none (`uv run jeff`) | story open | [BD-b5d125](../issues/BD-b5d1254a-7b4d-4703-920a-5d3e4965c796.json) |
| lafalce/system-one-model | Mateo Lafalce | Open weights | not stated | yes | CUDA documented (8 GB target); CPU/MPS not stated | none (`uv pip install -e .`) | not runnable here | — |
| NanoJev | TianyuCodings | Open weights | MIT | yes | CUDA only documented | none | not runnable here | — |
| Cua-S1 | Cua AI | Open weights, restricted | code MIT; checkpoints research/eval only | yes | nano: GPU ms-level, CPU under 100 ms; MPS/MLX not stated | none | story open | — |
| Geni-S1-Ops-26B-A4B-NVFP4 | Microland Ltd | Open weights | Apache-2.0 | yes | CUDA only (vLLM, DGX) | none | not runnable here | — |
| OpenJev (razorback16) | razorback16 | Open | Apache-2.0 per awesome list | not verified | not verified | not verified | not runnable here | — |

## Running on any hardware

"Runs on any hardware" is a harness property, not an engine property: each adapter is an optional
pip extra (`biased-decisions[laya]`, `[kev]`, `[von]`, and so on), so installing the base package
pulls in no engine's dependencies. A `device="auto"` resolver picks `cuda`, falls back to `mps`,
and falls back to `cpu`, with a flag to override it; an MLX adapter is Apple-silicon-only and
refuses to load anywhere else. Where a model ships more than one runtime for the same weights —
Laya's ONNX export and GGUF build alongside its PyTorch package, Bespoke-Nimble-9B's MLX build
alongside its CUDA one — the harness prefers the port built for the machine it is running on over
a slower general path through PyTorch. The cross-hardware runner and its one-command CLI are
tracked as [BD-87d960](../issues/BD-87d960e1-975a-46c6-8114-7d66cbbd8afa.json); the
parent epic for adding these engines is
[BD-4d86cf](../issues/BD-4d86cffe-b0df-44a9-b4ce-2074c5d30289.json).
