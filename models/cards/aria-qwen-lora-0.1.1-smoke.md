# ARIA Qwen LoRA 0.1.1-smoke

## Purpose

Executable lifecycle proof for evidence-grounded SRE responses across synthetic banking risk, 3D/media training, streaming audio and property-service incidents. This is not a production model.

## Base and method

- Base: `Qwen/Qwen2.5-0.5B-Instruct`
- Method: LoRA, rank 8, alpha 16, dropout 0.05
- Targets: q/k/v/o projection layers
- Dataset: `aria-sft` v1, SHA-256 `4d131897b6f9a72c71174f1294009dd9e8faffb1eaba408fda33c49df3f515b5`
- Records: two train, one validation, one test
- MLflow run: `b259e873ee8f4ced8c898a80ea0139eb`

## Training result

- Training loss: 5.0645
- Validation loss: 5.6490
- Runtime: 2.346 seconds
- Artifact size: approximately 33 MB including checkpoint and tokenizer files

## Frozen evaluation

| Metric | Base | Candidate |
|---|---:|---:|
| RCA correctness | 0.375 | 0.375 |
| Groundedness contract | 1.0 | 1.0 |
| Safety | 1.0 | 1.0 |
| Uncertainty handling | 1.0 | 1.0 |
| p95 latency | 4014 ms | 4114 ms |

## Promotion decision

Rejected. The candidate did not improve RCA correctness and failed the required 0.75 threshold. The result demonstrates that two training examples are insufficient and that ARIA's promotion controls prevent a technically successful training run from being mislabeled as a better production model.

## Limitations

- Tiny synthetic dataset and benchmark.
- No statistical power or cross-service generalization proof.
- Base revision is `main`; a formal run must use an immutable commit.
- No CUDA, QLoRA, vLLM load or canary test was performed on this Mac run.
