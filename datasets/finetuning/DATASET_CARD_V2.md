# ARIA SFT dataset v2

## Purpose

Teach concise, evidence-grounded, policy-aware incident analysis across synthetic banking, 2D/3D media, audio streaming, property, Kubernetes/GPU, and AI-security situations.

## Provenance and license

The records were authored specifically for this MIT-licensed repository from generic operational patterns. They contain no customer, employer, production, or proprietary data. Every record is marked `reviewed_synthetic`; that means repository-level technical review, not independent domain-expert certification.

## Processing

The builder validates schema and review status, scans and redacts secret patterns, deduplicates normalized conversations, creates deterministic splits, and records source and split SHA-256 hashes. The evaluation benchmark is separate and is not fed to training.

## Coverage and limitations

- 16 training-source records across six domains and four task types.
- Includes hard negatives, insufficient-evidence behavior, prompt injection, poisoning, and approval boundaries.
- Too small for a production model or statistically strong claims.
- Synthetic wording may cause style bias and cannot replace reviewed real incident data.
- The base model revision remains `main` for the local learning run and must be pinned to a commit for a formal release.
