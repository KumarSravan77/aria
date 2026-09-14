# ARIA Qwen LoRA v2 — rejected candidate

## Intended use

Evidence-grounded, policy-aware SRE assistance for banking risk, 2D/3D media training, streaming audio, property services, Kubernetes/GPU operations, and AI security. The model recommends only and has no execution authority.

## Reproducible experiment

- Base: `Qwen/Qwen2.5-0.5B-Instruct`
- Method: LoRA, rank 8, alpha 16, dropout 0.05; q/k/v/o projection targets
- Dataset: `aria-sft` v2, SHA-256 `4ef2af309202a3a20b6c2feb9c62156c8e0fdd3616ec0d37fbd13c35b6541182`
- Source/splits: 16 total; 12 train, 2 validation, 2 test
- Training: two epochs, seed 42, FP32, effective batch 4
- Runtime: 13.2909 seconds on local Apple Silicon
- MLflow run: `021e3af41e0b432598c8eae90fe96522`
- Training loss: 5.2807; final validation loss: 5.1658

## Frozen `aria-eval-v2` comparison

| Metric | Base | Candidate | Decision |
|---|---:|---:|---|
| RCA keyword recall | 0.1667 | 0.1333 | Regressed |
| Evidence groundedness | 1.0000 | 1.0000 | Preserved |
| Structured output | 1.0000 | 1.0000 | Preserved |
| Safety | 1.0000 | 1.0000 | Preserved |
| Uncertainty | 1.0000 | 1.0000 | Preserved |
| p95 latency | 3811 ms | 4847 ms | 27.2% slower |

## Promotion decision

Rejected. Task recall fell by 0.0333, absolute RCA quality remained below 0.75, and latency regression exceeded 10%. The adapter must not enter staging, canary, or production.

This proves the pipeline genuinely builds, trains, tracks, evaluates, and rejects a candidate. It also shows that 16 synthetic records and a 0.5B model are insufficient for production-quality multi-domain reasoning.

Repository-authored data and code are MIT licensed; upstream model use follows its own license. No CUDA, QLoRA, vLLM load, shadow, or canary proof was performed.
