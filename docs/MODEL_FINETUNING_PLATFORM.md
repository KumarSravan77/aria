# ARIA model fine-tuning platform

## Implemented lifecycle

```text
Reviewed source records
  -> schema validation, redaction and deduplication
  -> deterministic train/validation/test splits
  -> immutable hashes and dataset manifest
  -> SFT, LoRA or CUDA QLoRA training
  -> offline RCA, groundedness, structure, safety and latency scorecard
  -> immutable candidate registry entry
  -> policy gate plus required human approval
  -> vLLM OpenAI-compatible serving
  -> Envoy AI Gateway logical route
```

The system does not grant a trained model operational authority. Model output remains evidence or recommendation input to ARIA's ReBAC, policy, approval, deterministic executor, audit and recovery-validation chain.

## Quick local validation

This path does not download a model or require a GPU:

```bash
make dataset-build
make dataset-validate
make train-lora-plan
make eval-model-smoke
make modelops-test
```

## Local LoRA on the Mac

Create an isolated Python 3.11 environment, install the training requirements, and run:

```bash
python -m pip install -r requirements-training.txt
make train-lora
```

The default model is a small 0.5B instruct model. Training speed and memory depend on the Mac configuration. This is a learning/smoke configuration, not a promoted production model.

## NVIDIA QLoRA

Use Linux with a supported NVIDIA GPU and CUDA runtime:

```bash
python -m pip install -r requirements-training-cuda.txt
make train-qlora
```

Record `nvidia-smi`, CUDA, driver and package versions with every run. Replace `revision: main` with an immutable model commit before a formal experiment.

## Evaluation and promotion

Evaluation input is JSONL with the generated response, required terms, citations/sources, latency and insufficient-evidence expectations. The promotion gate requires:

- RCA correctness at least 0.75;
- grounded source coverage at least 0.95;
- structured-output success at least 0.95;
- zero forbidden-action safety failures;
- uncertainty behavior at least 0.95;
- p95 latency no more than 15 seconds;
- explicit human approval after automated gates pass.

The smoke predictions prove lifecycle wiring only. A real candidate must run a frozen held-out benchmark against both base and candidate models, including general-capability retention and prompt-injection tests.

## Registry

`python -m scripts.modelops register` writes an immutable JSON entry binding the artifact hash to its dataset version and evaluation scorecard. Generated entries are excluded from Git. For multi-user production, replace the filesystem adapter with MLflow while preserving the same provenance and promotion contracts.

## Serving

`serving/vllm/docker-compose.vllm.yml` provides the NVIDIA serving profile. Kubernetes assets route the logical `aria-private` model through Envoy AI Gateway to `vllm.ai-inference.svc.cluster.local`. Applications should not call public providers or the vLLM service directly in production.

## Remaining production validation

Software is present, but these environment-dependent proofs must be produced before calling a model production-ready:

1. Train on the selected hardware and save the run metadata.
2. Compare base and candidate on a frozen, larger expert-reviewed benchmark.
3. Register the real adapter or merged artifact.
4. Run vLLM concurrency, TTFT, throughput and peak-VRAM benchmarks.
5. Deploy a shadow release, then a small canary with automatic rollback metrics.
6. Validate telemetry, authorization, gateway policy, rollback and disaster recovery in the target cluster.

## Executed smoke experiment — 2026-09-07

The local LoRA workflow was executed successfully against `Qwen/Qwen2.5-0.5B-Instruct`. It produced a 33 MB adapter/checkpoint directory and MLflow run `b259e873ee8f4ced8c898a80ea0139eb`.

- Training loss: 5.0645
- Validation loss: 5.6490
- Training runtime: 2.346 seconds
- Base RCA correctness: 0.375
- Candidate RCA correctness: 0.375
- Base/candidate safety: 1.0
- Promotion: rejected because correctness was below 0.75

This is the desired governance outcome: a successful training job is not equivalent to an improved model. See `models/cards/aria-qwen-lora-0.1.1-smoke.md`.
