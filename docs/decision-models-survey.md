# System 1 / typed-decision models: survey for Biased-Decisions

Compiled 2026-09-23 from primary sources (GitHub, Hugging Face, PyPI, vendor docs). Claims carry a URL; throughput numbers are self-reported by each project unless stated. "Not found" means the source did not state it.

## Summary table

| Name | Maker | Hosted / open | Size | Licence | Per-option probabilities | Mac (MPS/MLX) / CPU / CUDA | pip | Source |
|---|---|---|---|---|---|---|---|---|
| Jev | TypeSafe AI | Hosted API (`POST https://api.typesafe.ai/v1/systemone`) | undisclosed | proprietary; SDK MIT | yes (noul/choice/score) | n/a (API) | `typesafe-sdk` | https://github.com/typesafe-ai/typesafe-sdk-python , https://typesafe.ai/blog/introducing-system-one-models-and-jev |
| Kev | Jared Palmer (individual) | Open weights | 0.8B / 4B / 9B (Qwen3.5 base + LoRA r16 + pointer head; older 0.6B/4B/8B on Qwen3) | Apache-2.0 | yes (noul/choice/score) | Mac: PyTorch bf16 on Qwen3 ckpts; Qwen3.5 ckpts have no MPS DeltaNet kernel, no MLX path yet / CPU: not stated / CUDA+ROCm: yes (flash-linear-attention) | no PyPI package; `uv sync --extra serve` from git | https://github.com/jaredpalmer/kev , https://huggingface.co/jaredpalmer/kev-4b |
| Laya | Convai Innovations | Open weights | 421M (ModernBERT-large + 2-layer head); multilingual 322M (mmBERT-base) | Apache-2.0 | yes (choice/score/noul + act/escalate) | CPU: yes (193-464 ms) / CUDA: yes / MPS: not stated; MLX via `laya-mlx` port; ONNX via receptron; GGUF via ggmlc (not llama.cpp) | `laya`, `laya-mlx` | https://huggingface.co/convaiinnovations/laya , https://pypi.org/project/laya/ , https://github.com/mizorewww/laya-mlx |
| Von | wfzyx (individual) | Open weights | 395M (ModernBERT-large) | Apache-2.0 | yes (choice/noul/score) | CUDA, ROCm, MPS, multithreaded CPU all listed | `von-sdk` | https://github.com/wfzyx/von , https://huggingface.co/wfzyx/von |
| System One Gemma | Akash Kamat (individual, not Google) | Open weights | 268M (Gemma 3 270M + scoring head, LoRA ~2.6M) | code Apache-2.0; weights CC-BY-NC-4.0 | yes (softmax over options; choice/binary/score) | CPU: yes; T4 tested; MPS/MLX not stated | none (clone + requirements.txt) | https://github.com/akash-kamat/system-one-gemma |
| Tiny-Jev | lostargon (individual) | Open weights | 596M (Qwen3-0.6B decoder stack) | Apache-2.0 | yes (choice/score/noul) | CUDA, MPS (`.to("mps")`), CPU | none; `transformers` + `trust_remote_code` | https://huggingface.co/lostargon/Tiny-Jev |
| Decider | Mapika | Open weights | 0.8B / 1.9B / 4.2B / 34.7B-A3B (Qwen3.5-Base), plus 2B-vision | Apache-2.0 | yes (choice 2-255 / score 2-10 / noul) | CUDA (bf16, CUDA graphs, FP8); MPS (fp16, merged 2026-09-22); CPU (bf16 eager) | `decider-ai` | https://github.com/Mapika/decider |
| this-that-model | FLock.io | Open weights | ~1.9B (adapted from decider-2b) | MIT (weights); decider base Apache-2.0 | yes | CUDA (RTX 5080), CPU fp32, MPS fp16 | none; `pip install -e .` | https://github.com/FLock-io/this-that-model , https://huggingface.co/flock-io/this-that-model-1.0 |
| Bespoke-Nimble-9B | Bespoke Labs | Open weights (LoRA ~165 MiB on Qwen3.5-9B) | 9B | Apache-2.0 | yes (boolean/enum up to 26/score) | MLX backend (M5 Pro 64GB: 444 ms median); CUDA bf16 (H100: 106 ms); CPU "limited" | none; requirements files | https://github.com/bespokelabsai/nimble , https://huggingface.co/bespokelabs/Bespoke-Nimble-9B |
| open-jev-deberta-v3-large | kotoba-lang / com-kotobalabs | Open weights | ~0.4B (DeBERTa-v3-large) | Apache-2.0 | yes (choice <=255 / score 2-10 / noul) | CPU (M1 Max fp32: ~1.8 s for 4 q); CUDA (H100: 28 ms for 10 q); MPS not stated | `pip install git+https://github.com/kotoba-lang/typed-decisions` | https://huggingface.co/com-kotobalabs/open-jev-deberta-v3-large |
| Verdict / openJev-verdict-2.0 (rlcd-modernbert-151m) | heman10x (individual) | Open weights | 151M (ModernBERT-base, gliclass-modern-base-v2.0) | Apache-2.0 | yes (choice up to 24 + abstain) | CPU via ONNX Runtime; WebGPU; PyTorch server; MPS not stated | none; `pip install -e .` from git | https://huggingface.co/heman10x/rlcd-modernbert-151m , https://github.com/Heman10x-NGU/Verdict-open-jev |
| jeff | logan-markewich (individual) | Open code; weights are Knowledgator GLiFormer | 400M (`knowledgator/gliformer-large-v1`) | MIT (code) | yes (temperature-scaled sigmoids; choice/score/noul) | auto CUDA -> MPS -> CPU; ONNX int8 CPU option | none; `uv run jeff` | https://github.com/logan-markewich/jeff |
| lafalce/system-one-model | Mateo Lafalce (individual) | Open weights | 149M (ModernBERT-base) | not stated | yes (softmax; choice/score/noul) | CUDA (8 GB GPU target); CPU/MPS not stated | none; `uv pip install -e .` | https://github.com/mateolafalce/system-one-model , https://huggingface.co/lafalce/system-one-model |
| NanoJev | TianyuCodings | Open weights | 0.6B (Qwen3-0.6B + heads) | MIT | yes (boolean sigmoid / score / choice 2-255) | CUDA only documented | none | https://github.com/TianyuCodings/NanoJev , https://huggingface.co/C-Tianyu/NanoJev |
| Cua-S1 (nano-0.1, 4b-0.1/0.2) | Cua AI | Open weights, restricted | nano ~855K params (byte-level encoder); 4b = LoRA on Qwen3.5-4B | code MIT; checkpoints research/eval only, commercial licence required | yes (softmax at option-letter positions) | nano: GPU ms-level, CPU <100 ms; MPS/MLX not stated | none | https://github.com/trycua/cua/blob/main/libs/cua-s1/MODEL_CARD.md , https://huggingface.co/cua-ai/cua-s1-nano-0.1 |
| Geni-S1-Ops-26B-A4B-NVFP4 | Microland Ltd | Open weights | 25.2B total / 3.8B active (DiffusionGemma), NVFP4 | Apache-2.0 | yes (choice) | CUDA only (vLLM, DGX) | none | https://huggingface.co/microlandltd/Geni-S1-Ops-26B-A4B-NVFP4 |
| OpenJev (razorback16) | razorback16 | Open | 26B-A4B (DiffusionGemma) | Apache-2.0 per awesome list | not verified | not verified | not verified | https://github.com/razorback16/openjev (listed in https://github.com/rajasekharponakala/awesome-system1-decision-models ; not fetched) |

## 1. Kev

- Maker: Jared Palmer (individual), not TypeSafe. Repo: https://github.com/jaredpalmer/kev . Announced on X as "Kev-0.5B: A tiny open source Jev-like decision model with a TypeSafe-compatible API based on Qwen2.5-0.5B" (https://x.com/jaredpalmer/status/2101028325472841920); the repo has since moved to Qwen3 (0.6B/4B/8B) and then Qwen3.5 (0.8B/4B/9B) bases (https://github.com/jaredpalmer/kev).
- Hosted or open: open weights, self-host. HF ids `jaredpalmer/kev-0.8b`, `jaredpalmer/kev-4b`, `jaredpalmer/kev-9b` (Qwen3.5) and `jaredpalmer/kev-0.6b`, `jaredpalmer/kev-4b@qwen3`, `jaredpalmer/kev-8b` (Qwen3) (https://github.com/jaredpalmer/kev). No hosted endpoint found.
- Licence: Apache-2.0 for adapter and head; Qwen3.5 base also Apache-2.0 (https://huggingface.co/jaredpalmer/kev-4b).
- Architecture: frozen base + rank-16 LoRA + pointer head; document and all questions packed into one prefill, questions masked from each other; packed vs isolated probabilities agree "within 4e-6 in fp32" (https://github.com/jaredpalmer/kev). Kev-4B has 33.8M trainable params; built-in temperature T=2.14, override with `KEV_TEMPERATURE=1.0` (https://huggingface.co/jaredpalmer/kev-4b).
- API shape: `POST /v1/systemone` implementing TypeSafe's public contract; question types `noul` (P(yes)), `choice` (per-option probabilities + confidence), `score` (distribution over levels + mean); response has model, answers, usage, latency ms (https://github.com/jaredpalmer/kev).
- Run: `git clone https://github.com/jaredpalmer/kev.git && cd kev && uv sync --extra serve && uv run --extra serve python -m kev.serve --run jaredpalmer/kev-4b --port 8009`; Python 3.12+, transformers >= 5.17, peft >= 0.21 (https://github.com/jaredpalmer/kev , https://huggingface.co/jaredpalmer/kev-4b).
- Hardware: CUDA and ROCm with `flash-linear-attention`. Apple silicon: repo README says Qwen3.5 4B/9B fit in 32 GB and reports "721 ms" per new state / "136 ms" cached prefix for Kev-4B on an M5 (https://github.com/jaredpalmer/kev); the kev-4b model card states "The DeltaNet kernels have no MPS implementation; PyTorch falls back to reference code", a five-question request takes 0.78 s on M5 bf16 versus 0.17 s for the Qwen3 checkpoint, and recommends the Qwen3 checkpoint on Apple silicon "until an MLX path exists" (https://huggingface.co/jaredpalmer/kev-4b). CPU: not stated.
- Accuracy (new-source dev set): Kev-9B 0.852, Kev-4B 0.837, Kev-0.8B 0.684; Brier 0.237 / 0.255 / 0.460; hosted Jev 0.857 on the same comparison (https://github.com/jaredpalmer/kev). Third-party write-up gives training cost of about $95 in Modal H100 time (https://aiweekly.co/alerts/jared-palmer-ships-kev-an-apache-20-jev-style-decision-model-family-built-on).
- Name collision: https://kev-notjev.vercel.app/ ("NotJev: Kev") is a different project, an npm `@kev-ai/server` router that calls Ollama/vLLM/OpenAI-compatible backends with the user's own model; it is not Palmer's weights.

## 2. Gemma-branded decision model

- No official Google/DeepMind "DecisionGemma", "Gemma judge" or "Gemma System One" model was found. The Google Gemma variants page lists Gemma 4, EmbeddingGemma, ShieldGemma 2, Gemma 3n, DiffusionGemma, FunctionGemma, PaliGemma, RecurrentGemma, DataGemma, Gemma-APS; none is a typed-decision model (https://ai.google.dev/gemma/docs).
- Closest community items:
  - System One Gemma (Akash Kamat): Gemma 3 270M + scoring head; choice/binary/score; softmax probabilities; "~50ms" per decision; CPU fine, trained on a Colab T4; code Apache-2.0, weights CC-BY-NC-4.0; base id `google/gemma-3-270m` requires Gemma licence acceptance (https://github.com/akash-kamat/system-one-gemma).
  - DiffusionGemma-based classifiers: DiffusionGemma is Google DeepMind's open-weight text diffusion model, `google/diffusiongemma-26B-A4B-it`, 25.2B total / 3.8B active, Apache-2.0 (https://ai.google.dev/gemma/docs/diffusiongemma , https://huggingface.co/google/diffusiongemma-26B-A4B-it). A Google Cloud community post describes a Jev-style classifier on it with vLLM (https://medium.com/google-cloud/how-to-build-a-jev-style-classifier-with-diffusiongemma-and-vllm-ef2e0bfa9ad7 ; returned HTTP 403 when fetched, contents not verified). Derived models: Geni-S1-Ops (Microland, CUDA/vLLM only, https://huggingface.co/microlandltd/Geni-S1-Ops-26B-A4B-NVFP4), djev (https://github.com/Davipar/djev-dev), openjev razorback16 (https://github.com/razorback16/openjev). None is runnable on Mac/CPU as documented.
  - system-one-open (mithalouni), Gemma 2B-E2B base, listed at https://github.com/andyrewlee/awesome-system-one ; not fetched, details not verified.

## 3. Other Laya-like models (per-model notes)

Laya (Convai Innovations). Three checkpoints: `convaiinnovations/laya` (ModernBERT-large 395M + 2-layer head = 421M, 512 ctx), `convaiinnovations/laya-multilingual` (mmBERT-base, 322M, 1024 ctx, 100+ languages), `convaiinnovations/laya-typed-decisions` (fine-tuned, 0.766 acc, ECE 0.081). Each option scored at its own `[MASK]` token then softmaxed; trained with RLCD against proper scoring rules. T4: 32.8-39.5 ms single question, 7.2 ms/q at 10 batched; CPU 193-464 ms. `pip install laya`, `Router(preload=True).predict(state, questions)`; server device via `LAYA_DEVICE=cuda`; MPS not documented (https://huggingface.co/convaiinnovations/laya , https://pypi.org/project/laya/ , https://github.com/NandhaKishorM/laya). The convaiinnovations HF org has no other decision models (other repos: qwen FastAPI demos, kidney-exchange-ppo, shoeguard-safety-slm, medgemma-ecg) (https://huggingface.co/convaiinnovations). Ports: `laya-mlx` (PyPI; M3 Max 13.42 ms single short question fp16, 146.8 q/s at batch 64; 378/378 answer parity with PyTorch; deterministic over 100 repeated calls; weights `aac6fef/laya-mlx`, `aac6fef/laya-multilingual-mlx`, `aac6fef/laya-typed-decisions-mlx`) (https://github.com/mizorewww/laya-mlx , https://huggingface.co/aac6fef/laya-mlx); ONNX export `receptron/laya-onnx` for Node/onnxruntime, max logit diff ~1e-5 vs PyTorch, outputs `logits [B,K]` and `act_probs [B,2]` (https://huggingface.co/receptron/laya-onnx , https://github.com/receptron/laya); GGUF `mys/laya-GGUF` runs with the ggmlc `laya` binary, not llama.cpp, RTX 4050 ~25 ms per noul (https://huggingface.co/mys/laya-GGUF).

Von (wfzyx). ModernBERT-large 395M, Apache-2.0, `pip install von-sdk`, `von serve`; CUDA, ROCm, MPS, CPU; choice/noul/score with `probabilities` field; ~18 ms on T4; deterministic (https://github.com/wfzyx/von).

Tiny-Jev (lostargon). Qwen3-0.6B decoder, 596M, Apache-2.0, `AutoModel.from_pretrained("lostargon/Tiny-Jev", trust_remote_code=True)`; CUDA/MPS/CPU; 20-50 ms on M-series; choice/score/noul; ECE 0.004 after temperature calibration; 4096-token context (https://huggingface.co/lostargon/Tiny-Jev).

Decider (Mapika). Qwen3.5-Base 0.8B/2B/4B/35B-A3B + vision; Apache-2.0; `pip install decider-ai`; CUDA bf16 with CUDA graphs and optional FP8, MPS fp16 merged 2026-09-22, CPU bf16 eager; memory 2B ~4 GB, 4B 8.4 GB, 35B 65 GB; held-out acc 0.755/0.788/0.810; one distribution per question (https://github.com/Mapika/decider).

this-that-model (FLock.io). ~1.9B adapted from decider-2b, MIT weights, `TypedDecider.from_pretrained("flock-io/this-that-model-1.0")`; CUDA/CPU fp32/MPS fp16; ~33 ms on RTX 5080 laptop; GGUF mirror `mradermacher/this-that-model-1.0-GGUF` (https://github.com/FLock-io/this-that-model , https://modelsystem.one/models/this-that/).

Bespoke-Nimble-9B (Bespoke Labs). LoRA on Qwen3.5-9B, Apache-2.0; `ParallelScorer(model_path).score(text, schema)`; softmax over candidate logits with fitted T=2.179; MLX backend on Mac (M5 Pro 64 GB: 444 ms median), CUDA bf16 (H100: 106 ms); CPU "limited"; no pip package (https://github.com/bespokelabsai/nimble , https://huggingface.co/bespokelabs/Bespoke-Nimble-9B).

open-jev-deberta-v3-large (kotoba-lang). DeBERTa-v3-large ~0.4B, Apache-2.0, `OpenJev.from_pretrained(...).decide(state, questions)`; CPU M1 Max fp32 ~1.8 s for 4 questions; H100 28 ms for 10; in-domain acc 0.854, ECE 0.022 (https://huggingface.co/com-kotobalabs/open-jev-deberta-v3-large).

Verdict / rlcd-modernbert-151m (heman10x). ModernBERT-base 151M, Apache-2.0; `DecisionEngine().evaluate(context, queries)`; CPU via ONNX Runtime, WebGPU, PyTorch; p50 35.58 ms; up to 24 options + abstain; T=1.0716 (https://huggingface.co/heman10x/rlcd-modernbert-151m).

jeff (logan-markewich). GLiFormer 400M (`knowledgator/gliformer-large-v1`), MIT code; auto CUDA -> MPS -> CPU, `JEFF_DEVICE` override, ONNX int8 CPU; choice/score/noul; sigmoid probabilities temperature-scaled at 3.2; P50 151 ms on L4 via HTTP (https://github.com/logan-markewich/jeff).

lafalce/system-one-model. ModernBERT-base 149M; `/v1/systemone` server; softmax probabilities, entropy confidence; 8 GB GPU target; licence not stated (https://github.com/mateolafalce/system-one-model).

NanoJev (TianyuCodings). Qwen3-0.6B + heads, MIT, `C-Tianyu/NanoJev`; CUDA only documented; game-decision focus (https://github.com/TianyuCodings/NanoJev).

Cua-S1 (Cua AI). nano-0.1 is an ~855K-param byte-level option-attention classifier; 4b variants are LoRA on Qwen3.5-4B; code MIT, checkpoints research/eval only; GUI decision tasks; nano CPU <100 ms (https://github.com/trycua/cua/blob/main/libs/cua-s1/MODEL_CARD.md).

Directories used: https://github.com/rajasekharponakala/awesome-system1-decision-models , https://github.com/andyrewlee/awesome-system-one , https://modelsystem.one/ (16 models incl. mini-jev, djev-spark, jevlike, reflex, openjev by Alex Wortega, not individually verified here), https://github.com/fstandhartinger/jevbench (40+ systems).

## 4. Runtime matrix (determinism and Mac throughput where stated)

| Model | MPS | MLX | CPU | CUDA | pip | Probabilities vs label | Deterministic | M-series ms/text (stated) |
|---|---|---|---|---|---|---|---|---|
| Kev (Qwen3 ckpts) | yes bf16 | no | not stated | yes | no | probabilities | packed==isolated within 4e-6 fp32 | 0.17 s / 5 q on M5 (kev-4b card) |
| Kev (Qwen3.5 ckpts) | fallback, slow | no | not stated | yes | no | probabilities | same | 0.78 s / 5 q on M5; 721 ms new state, 136 ms cached |
| Laya (PyTorch) | not stated | via laya-mlx | yes | yes | yes | probabilities | not stated | not stated |
| laya-mlx | n/a | yes | n/a | n/a | yes | probabilities | 100 repeated calls identical | 13.42 ms single q, M3 Max |
| Von | yes | no | yes | yes | yes | probabilities | yes (stated) | not stated |
| Tiny-Jev | yes | no | yes | yes | no | probabilities | not stated | 20-50 ms |
| Decider | yes fp16 | no | yes | yes | yes | probabilities | not stated | not stated |
| this-that | yes fp16 | no | yes | yes | no | probabilities | not stated | not stated |
| Nimble | no | yes | limited | yes | no | probabilities | "no sampling" | 444 ms median, M5 Pro |
| open-jev-deberta | not stated | no | yes | yes | git | probabilities | not stated | ~450 ms/q (1.8 s / 4 q, M1 Max CPU) |
| Verdict 151M | not stated | no | ONNX | PyTorch | git | probabilities + abstain | not stated | not stated |
| jeff | yes | no | yes + ONNX | yes | no | probabilities | not stated | not stated |
| System One Gemma | not stated | no | yes | yes | no | probabilities | "deterministic" | not stated (~50 ms, hardware unspecified) |
| Geni-S1-Ops | no | no | no | vLLM only | no | probabilities | not stated | n/a |

## 5. Comparators: option-token logprobs from open LLMs

Mechanism: give the model the text plus a prompt whose answer is a single option token (A/B/C or yes/no), take the next-token logits, restrict to the option tokens, softmax. One forward pass, no decoding, deterministic given fixed weights and dtype.

- transformers (MPS, CPU, CUDA): `model(**inputs).logits[:, -1, :]` gives full-vocab logits on any torch device; ModernBERT and Gemma/Llama/Qwen are supported (https://huggingface.co/docs/transformers/model_doc/modernbert). lm-evaluation-harness uses exactly this path for `loglikelihood` / `multiple_choice` tasks on `--device cuda|cpu|mps` (https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/interface.md , https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/models/huggingface.py). Cheapest to code; Mac speed limited by MPS.
- mlx-lm (Apple silicon only): `model(inputs)` returns full-vocab logits; `generate_step` yields `(token, logprobs)` per step with a full log-prob vector (https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/generate.py). The server's `/v1/chat/completions` accepts `logprobs` 1-10 and returns `token_logprobs` / `top_logprobs` (https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/SERVER.md); open issue #1358 requests per-token logprobs from `batch_generate()` (https://github.com/ml-explore/mlx-lm/issues/1358). Fastest on Mac; no CPU/CUDA.
- llama.cpp (Metal default on macOS, CPU, CUDA `-DGGML_CUDA=ON`) (https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md): `/completion` with `n_probs` returns `completion_probabilities` with top-N `logprob` per token; `post_sampling_probs` switches to post-sampling `prob` (https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md). Limitation: no gather-by-token-id; you widen `n_probs` and match returned tokens by text; OpenAI-compatible chat path capped at `top_logprobs=20` upstream (https://github.com/ollama/ollama/pull/18580 , https://github.com/NousResearch/hermes-agent/issues/118599). Python: `llama-cpp-python` with `CMAKE_ARGS="-DGGML_METAL=on"` or `-DGGML_CUDA=on`, `logprobs` parameter on completions (https://llama-cpp-python.readthedocs.io/). One GGUF runs on all three hardware targets.
- Recommendation for the harness: transformers adapter as the portable baseline (one code path, all three devices), mlx-lm adapter as the Mac fast path, llama.cpp adapter for GGUF fallback; all three expose the same option-logit softmax.

## 6. Cross-hardware packaging patterns and recommendation

- lm-evaluation-harness: single CLI, `--model hf|vllm|gguf|...`, `--device cuda|cpu|mps`, `--batch_size auto`; backends selected by name, dependencies as extras (`hf`, `vllm`, `onnxruntime`, `optimum`, `litellm`, `api`) (https://github.com/EleutherAI/lm-evaluation-harness/blob/main/pyproject.toml , https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/interface.md). Interface docs mention `mlx` in examples but `lm_eval/models/` has no mlx backend file (https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/models). MPS note: verify CPU and MPS forward passes match (https://github.com/EleutherAI/lm-evaluation-harness).
- JevBench: adapter classes `typesafe`, `systemone_list`, `gradio_space`, `local_openjev`, `openai_compat`; HTTP adapters need only stdlib; no MLX/ONNX/GGUF handling (https://github.com/fstandhartinger/jevbench).
- HELM: `pip install crfm-helm` plus extras scripts; device handling not stated on the README (https://github.com/stanford-crfm/helm). BBQ repo has no harness (https://github.com/nyu-mll/BBQ).
- Laya ecosystem already splits by runtime package: `laya` (torch), `laya-mlx` (MLX), `@receptron/laya` (ONNX), ggmlc GGUF.

Recommended pattern (ten lines):
1. One `Engine` protocol: `decide(text, question) -> {option: prob}`; every adapter returns probabilities, never labels.
2. Adapters as optional extras: `pip install biased-decisions[jev]` (typesafe-sdk), `[laya]` (laya), `[laya-mlx]`, `[kev]` (git+transformers+peft), `[von]`, `[decider]`, `[hf]` (transformers option-logprob comparator), `[mlx]` (mlx-lm), `[gguf]` (llama-cpp-python).
3. `device="auto"` resolves cuda -> mps -> cpu via torch; a `--device` flag overrides; mlx adapter is Mac-only and refuses elsewhere.
4. Prefer MLX/GGUF adapters for the same weights on Mac when a port exists (laya-mlx, Nimble MLX, this-that GGUF); fall back to torch.
5. Record `engine, model_id, revision, device, dtype, temperature` in every result row for reproducibility.
6. Fix dtype per device (fp32 on CPU, fp16 on MPS, bf16 on CUDA) and log it; add a parity check job that compares CPU vs accelerator probabilities on a fixed sample (lm-eval's MPS advice).
7. Expose calibration knobs (`KEV_TEMPERATURE`, Laya temperature) as adapter config so raw and calibrated probabilities are both reportable.
8. Keep hosted adapters (Jev) stdlib-only like JevBench so the base install has no torch.
9. One CLI: `biased-decisions run --engine laya --device auto --dataset bios`; engines register via entry points.
10. CI matrix: macos-latest (mps, mlx), ubuntu CPU, and a CUDA runner, each running the smallest model (Laya 322M / Tiny-Jev / Von) end to end.

## Not found

- Any hosted Kev API; any Kev PyPI package; Kev CPU latency.
- Any official Google "DecisionGemma" / "Gemma judge" / Gemma System One model.
- Laya MPS support statement or M-series latency for the PyTorch package (only laya-mlx numbers).
- Other decision models from convaiinnovations besides the three Laya checkpoints.
- Licence for lafalce/system-one-model; Von, Decider, this-that, Verdict, jeff Mac throughput numbers.
- Determinism statements for Laya (PyTorch), Decider, this-that, Tiny-Jev, open-jev-deberta.
- Verified details for OpenJev (razorback16), system-one-open (mithalouni), djev, mini-jev, jevlike, reflex, Tiny-Jev MLX port; Cua-S1 device support.
- Google Cloud Medium DiffusionGemma article contents (HTTP 403).
- An mlx backend in lm-evaluation-harness (docs mention it; no source file present).
