---
name: aria-open-model-finetuning-expert
description: End-to-end expert operating skill for designing, training, evaluating, serving, observing, securing, and continuously improving open-source language models for ARIA.
user-invocable: true
---

# ARIA Open-Source Model Fine-Tuning Expert

## 0. Mission

Use this skill whenever work involves open-source model selection, dataset engineering, post-training, fine-tuning, preference optimization, reinforcement learning, distillation, quantization, model evaluation, model serving, model routing, LLM observability, model registry, training infrastructure, or continuous model improvement for ARIA.

The objective is not merely to make a training job run. The objective is to build a reproducible, measurable, safe, production-grade model engineering system in which every model change can be explained, evaluated, promoted, observed, and rolled back.

ARIA's model lifecycle must follow this invariant:

```text
Problem definition
→ baseline
→ data contract
→ dataset build
→ contamination checks
→ training experiment
→ offline evaluation
→ safety evaluation
→ serving evaluation
→ staging/canary
→ production
→ monitoring
→ feedback
→ retraining only when justified
```

Never treat fine-tuning as the default solution. First determine whether the problem should be solved with prompting, structured output, RAG, MCP/tools, routing, a larger/better base model, or fine-tuning.

---

# 1. ARIA Safety Invariant

Model training must never weaken ARIA's existing control boundary.

```text
Model recommends
→ ReBAC authorizes
→ policy validates
→ approval gates
→ deterministic executor mutates
→ recovery validation confirms
→ operational memory records
```

A fine-tuned model is still untrusted probabilistic software.

Never:

- grant a model direct production shell access;
- allow generated text to execute as infrastructure commands without deterministic validation;
- bypass OpenFGA/ReBAC, policy, approval, or executor controls;
- train secrets, credentials, private keys, access tokens, or confidential payloads into model weights;
- promote a candidate because training loss decreased;
- use production evaluation examples in training;
- automatically retrain from raw production feedback without curation and evaluation;
- treat a model's self-reported confidence as calibrated confidence.

For ARIA, remediation proposals remain recommendations. Execution remains policy-controlled.

---

# 2. ARIA Repository Integration

Keep model engineering as a first-class subsystem of the existing ARIA repository.

Target structure:

```text
aria/
├── server/
│   ├── llm/
│   ├── agents/
│   ├── agent_runtime/
│   ├── rag/
│   ├── evals/
│   ├── ai_observability/
│   ├── safety/
│   ├── authz/
│   ├── healing/
│   └── cost/
│
├── datasets/
│   ├── raw/
│   ├── curated/
│   ├── sft/
│   ├── preference/
│   ├── reward/
│   ├── rl/
│   ├── evaluation/
│   └── manifests/
│
├── training/
│   ├── common/
│   ├── sft/
│   ├── lora/
│   ├── qlora/
│   ├── dpo/
│   ├── kto/
│   ├── grpo/
│   ├── rloo/
│   ├── reward_model/
│   ├── distillation/
│   ├── continued_pretraining/
│   ├── distributed/
│   │   ├── ddp/
│   │   ├── fsdp/
│   │   └── deepspeed/
│   ├── quantization/
│   ├── configs/
│   │   ├── trl/
│   │   └── axolotl/
│   └── pipelines/
│
├── evaluation/
│   ├── benchmarks/
│   ├── rca/
│   ├── tool_use/
│   ├── structured_output/
│   ├── rag/
│   ├── hallucination/
│   ├── safety/
│   ├── calibration/
│   ├── latency/
│   ├── regression/
│   └── reports/
│
├── models/
│   ├── registry/
│   ├── manifests/
│   ├── adapters/
│   └── cards/
│
├── serving/
│   ├── vllm/
│   ├── adapters/
│   ├── inference_pool/
│   └── envoy/
│
├── k8s/
│   └── ai-gateway/
│
└── skills/
    └── aria-model-finetuning-expert/
        └── SKILL.md
```

Do not duplicate ARIA's existing `server/evals`, `server/llm`, `server/ai_observability`, safety, or gateway logic. Extend those boundaries.

---

# 3. The First Decision: Should ARIA Fine-Tune?

Use this order before starting training.

## 3.1 Prompting first

Use prompt/system instruction changes when the issue is primarily:

- tone;
- response format;
- explicit workflow steps;
- missing constraints that can fit in context;
- deterministic schema requirements;
- simple instruction-following differences.

## 3.2 Structured generation second

Use JSON schema / constrained decoding when the problem is malformed output, not missing knowledge.

For ARIA, RCA and remediation outputs should prefer deterministic schemas such as:

```json
{
  "incident_type": "deployment_regression",
  "root_cause": "...",
  "confidence": 0.91,
  "evidence": [],
  "recommended_actions": [],
  "risk": "medium",
  "requires_approval": true
}
```

## 3.3 RAG when knowledge changes

Prefer RAG when the desired behavior requires facts that are:

- frequently updated;
- organization-specific;
- too large for weights;
- auditable/citable;
- subject to authorization;
- removable on demand.

Examples:

- current runbooks;
- service topology;
- current deployment state;
- incident history;
- internal documentation;
- Kubernetes state;
- current SLO configuration.

## 3.4 MCP/tools when actions or live state are needed

Use tools rather than model weights for:

- Prometheus queries;
- Kubernetes inspection;
- log search;
- trace lookup;
- GitHub actions;
- cloud APIs;
- Dynatrace queries;
- remediation execution.

## 3.5 Model routing when capability differences solve the problem

Before training, compare several capable base models behind Envoy AI Gateway. A routing change may solve the issue more cheaply than training.

## 3.6 Fine-tune when behavior is the problem

Fine-tune when ARIA needs repeatable learned behavior such as:

- incident classification;
- domain terminology;
- stable RCA structure;
- tool-selection patterns;
- SRE reasoning style;
- concise operational responses;
- policy-aware recommendations;
- preference toward evidence-backed responses;
- improved performance on a narrow benchmark.

## 3.7 Continued pretraining when domain language is deeply missing

Use continued/domain-adaptive pretraining only when the base model systematically lacks the domain distribution and you possess a sufficiently large high-quality corpus. This is different from SFT.

---

# 4. Core Transformer Concepts to Master

Do not fine-tune mechanically. Understand the model.

## 4.1 Tokens and tokenization

Know:

- vocabulary;
- subword tokenization;
- BPE/Unigram-style tokenization;
- special tokens;
- BOS/EOS;
- padding token;
- unknown tokens where applicable;
- token fertility;
- bytes vs characters vs tokens;
- tokenizer-model compatibility;
- chat-template compatibility.

Always measure dataset token lengths before training.

## 4.2 Embeddings

Understand:

- token embeddings;
- positional representation;
- hidden size;
- embedding matrix;
- tied vs untied output embeddings.

## 4.3 Attention

Understand:

- query, key, value;
- scaled dot-product attention;
- causal masking;
- self-attention;
- multi-head attention;
- grouped-query attention (GQA);
- multi-query attention (MQA);
- KV cache;
- attention complexity;
- long-context memory cost.

## 4.4 Position encoding

Understand:

- absolute position embeddings;
- RoPE;
- RoPE scaling;
- context extension tradeoffs;
- position interpolation concepts.

Do not change context length blindly.

## 4.5 MLP/feed-forward blocks

Understand:

- hidden/intermediate dimensions;
- activation functions;
- SwiGLU/GEGLU-style blocks;
- why LoRA target selection may include MLP linear layers.

## 4.6 Normalization

Understand LayerNorm/RMSNorm conceptually and the role of numerical stability.

## 4.7 Dense vs Mixture-of-Experts

Know:

- dense parameter count;
- total vs active MoE parameters;
- router/gating;
- experts;
- load balancing;
- expert parallelism;
- implications for LoRA and quantization.

## 4.8 Logits and probabilities

Understand:

- logits;
- softmax;
- temperature;
- top-k;
- top-p;
- greedy decoding;
- beam-search limitations for chat models;
- sampling vs training objectives.

## 4.9 Cross-entropy loss

Know what next-token prediction loss means and why lower loss does not automatically equal better task behavior.

## 4.10 Perplexity

Know its relationship to cross entropy and its limitations for instruction-following evaluation.

---

# 5. Model Types and Selection

Classify candidate models by:

- base/pretrained vs instruct/chat;
- dense vs MoE;
- parameter count;
- active parameter count;
- context length;
- tokenizer;
- language coverage;
- coding capability;
- tool/function calling capability;
- structured-output capability;
- license;
- commercial-use constraints;
- redistribution requirements;
- model-card safety constraints;
- architecture support in Transformers/PEFT/vLLM/Axolotl;
- quantization support;
- GPU memory requirements.

For ARIA, benchmark at least three distinct model families rather than assuming one family is universally best.

Model selection record:

```yaml
model_id: <hub/model>
revision: <commit-or-tag>
license: <license>
model_type: instruct
architecture: <architecture>
parameters_total: <n>
parameters_active: <n-or-null>
context_length: <n>
tokenizer_revision: <revision>
chat_template_hash: <sha256>
intended_aria_tasks:
  - rca
  - tool_selection
known_constraints: []
```

Pin exact revisions for reproducibility.

---

# 6. Data Engineering: The Most Important Part

Model quality is usually bounded by data quality.

## 6.1 ARIA data sources

Potential sources:

- reviewed incident reports;
- postmortems;
- runbooks;
- sanitized alert payloads;
- Kubernetes issue datasets;
- synthetic incident simulations;
- chaos experiment results;
- approved RCA drafts;
- reviewed remediation recommendations;
- agent traces;
- tool-selection traces;
- human preference feedback;
- public SRE datasets with compatible licenses.

Do not directly ingest unreviewed model-generated output as ground truth.

## 6.2 Dataset stages

```text
raw
→ normalized
→ redacted
→ deduplicated
→ quality-scored
→ labeled
→ split
→ versioned
→ frozen
```

## 6.3 Dataset manifest

Every dataset release must have:

```yaml
dataset_name: aria-rca-sft
version: 1.0.0
created_at: <timestamp>
sources: []
license_summary: []
record_count: 0
token_count: 0
train_count: 0
validation_count: 0
test_count: 0
schema_version: 1
redaction_version: 1
dedupe_version: 1
split_strategy: incident_group
sha256: <hash>
known_limitations: []
```

## 6.4 Normalization

Normalize:

- timestamps;
- service names;
- environment labels;
- severity;
- cloud region notation;
- Kubernetes object references;
- metric names;
- incident categories;
- structured evidence.

Preserve meaningful technical distinctions.

## 6.5 Redaction

Remove or replace:

- passwords;
- API keys;
- bearer tokens;
- cookies;
- private keys;
- database credentials;
- secret environment variables;
- customer identifiers not required for training;
- sensitive URLs/query strings;
- proprietary payloads that are not approved for model training.

Redaction must occur before external model-assisted labeling.

## 6.6 Deduplication

Perform:

- exact dedupe;
- normalized exact dedupe;
- near-duplicate detection;
- semantic duplicate review;
- template boilerplate removal.

Duplicates can distort loss and leak evaluation examples.

## 6.7 Data contamination

Check for overlap between:

- train and validation;
- train and test;
- source incident and derived paraphrases;
- synthetic variants of the same scenario;
- public benchmark data and model training corpora where known.

For incidents, split by incident family/service/time group, not random individual messages, when correlated records exist.

## 6.8 Data quality scoring

Possible dimensions:

- correctness;
- completeness;
- evidence quality;
- action safety;
- schema validity;
- source provenance;
- reviewer confidence;
- ambiguity;
- duplication risk.

Reject low-quality records rather than compensating with more epochs.

## 6.9 Dataset balance

Inspect distributions across:

- incident type;
- severity;
- service;
- cloud;
- Kubernetes failure mode;
- easy/hard cases;
- safe vs unsafe recommendations;
- tool usage;
- no-action-needed cases.

Avoid teaching ARIA that every incident requires restart/rollback.

## 6.10 Curriculum

Potential sequence:

```text
simple classification
→ evidence extraction
→ RCA
→ remediation recommendation
→ tool selection
→ multi-step investigation
```

Use curriculum only when validated experimentally.

---

# 7. Chat Templates and Formatting

Chat templates are part of the model contract.

Know:

- system/user/assistant roles;
- tool roles;
- assistant generation prompt;
- EOS behavior;
- tokenizer `apply_chat_template` semantics;
- template differences across model families.

Never train one format and serve another without validating it.

Record the template hash with each model version.

Example SFT record:

```json
{
  "messages": [
    {"role": "system", "content": "You are ARIA's evidence-grounded SRE incident analysis model."},
    {"role": "user", "content": "<normalized incident context>"},
    {"role": "assistant", "content": "<reviewed response>"}
  ]
}
```

For tool-use training, use the exact tool-call schema the serving model will receive.

---

# 8. Training Objectives

## 8.1 Causal language modeling

Next-token prediction over a sequence.

## 8.2 Completion-only loss

For SFT, consider masking prompt/user tokens so loss is focused on assistant completion, when supported and appropriate.

## 8.3 Packed training

Packing combines shorter examples into longer sequences to improve utilization. Validate that boundaries/EOS tokens are correct and that packing does not create unintended cross-example semantics.

## 8.4 Sequence length

Choose based on measured dataset percentiles, not model maximum alone.

Track:

- p50;
- p90;
- p95;
- p99;
- max tokens;
- truncation rate.

Longer sequence length increases memory and compute substantially.

---

# 9. Supervised Fine-Tuning (SFT)

SFT teaches the model to imitate reviewed target behavior.

Use for:

- RCA style;
- JSON outputs;
- domain language;
- evidence citation format;
- tool selection examples;
- operational response quality.

Understand:

- full fine-tuning;
- parameter-efficient fine-tuning;
- epochs;
- steps;
- learning rate;
- warmup;
- scheduler;
- weight decay;
- optimizer;
- batch size;
- gradient accumulation;
- gradient clipping;
- validation frequency;
- checkpoint frequency;
- early stopping criteria.

Always compare against the untouched base model.

---

# 10. Full Fine-Tuning

Full fine-tuning updates most/all model parameters.

Advantages:

- maximum adaptation capacity;
- no adapter dependency at inference.

Costs/risks:

- much higher VRAM/compute;
- larger checkpoints;
- greater catastrophic forgetting risk;
- harder multi-task specialization;
- more expensive experimentation.

Do not use full fine-tuning merely because GPUs are available. Demonstrate that PEFT is insufficient first.

---

# 11. LoRA

LoRA freezes base weights and learns low-rank updates.

Conceptually:

```text
W' = W + ΔW
ΔW = B × A
rank(ΔW) <= r
```

Master:

- rank `r`;
- `lora_alpha`;
- scaling;
- `lora_dropout`;
- target modules;
- bias handling;
- adapter initialization;
- modules-to-save;
- adapter merge;
- multiple adapters;
- adapter composition where supported.

## 11.1 Rank

Higher rank increases adapter capacity and parameter count. Do not assume higher is better.

Experiment with a controlled grid such as:

```text
r = 8, 16, 32, 64
```

while holding other variables fixed.

## 11.2 Alpha

Understand the effective update scaling. Record alpha/r relationships rather than copying defaults blindly.

## 11.3 Target modules

Possible targets include attention and MLP linear layers. `all-linear` is common for QLoRA-style adaptation, but architecture compatibility must be verified.

## 11.4 Merge vs unmerged

Unmerged adapter:

```text
base model + adapter at runtime
```

Merged:

```text
base weights + learned delta → standalone merged checkpoint
```

Retain provenance either way.

---

# 12. QLoRA

QLoRA combines a quantized frozen base model with trainable LoRA adapters.

Understand:

- 4-bit loading;
- NF4 concepts;
- double quantization concepts;
- compute dtype vs storage dtype;
- paged optimizer concepts;
- quantization error;
- memory savings;
- limitations by architecture/backend.

QLoRA reduces memory; it does not make training free.

Benchmark quality against LoRA/full fine-tuning when the task warrants it.

---

# 13. PEFT Variants Beyond Basic LoRA

Know the conceptual landscape even when ARIA initially standardizes on LoRA/QLoRA:

- AdaLoRA;
- IA3;
- prompt tuning;
- prefix tuning;
- LoRA variants such as rank-stabilized approaches;
- DoRA-style decomposition;
- adapter initialization methods;
- architecture-specific MoE adapter strategies.

Do not introduce a variant without a benchmarkable hypothesis.

---

# 14. Optimizers

Understand:

- AdamW;
- optimizer states;
- beta parameters;
- epsilon;
- weight decay;
- 8-bit optimizer concepts;
- newer optimizers only when supported and justified.

Model memory includes more than weights:

```text
weights
+ gradients
+ optimizer states
+ activations
+ temporary buffers
```

---

# 15. Learning Rate

Learning rate is one of the most important hyperparameters.

Symptoms of too high:

- unstable loss;
- NaN/Inf;
- rapid forgetting;
- validation degradation;
- output collapse.

Symptoms of too low:

- almost no task improvement;
- extremely slow convergence.

Tune separately for full fine-tuning vs LoRA/QLoRA.

Always log the complete scheduler curve.

---

# 16. Batch Size and Gradient Accumulation

Distinguish:

- per-device microbatch size;
- number of devices;
- gradient accumulation steps;
- effective global batch size.

Conceptually:

```text
effective batch
= microbatch × gradient_accumulation × data_parallel_world_size
```

When sequence lengths vary, token-based batch characteristics matter too.

---

# 17. Precision

Understand:

- FP32;
- FP16;
- BF16;
- FP8 concepts;
- lower-precision quantized storage.

Prefer BF16 on hardware with robust BF16 support for many modern LLM training workloads. Validate hardware and framework support.

Know:

- loss scaling concepts for FP16;
- overflow/underflow;
- numerical stability.

---

# 18. Gradient Concepts

Master:

- forward pass;
- backward pass;
- automatic differentiation;
- gradients;
- gradient norm;
- gradient clipping;
- exploding gradients;
- vanishing gradients conceptually;
- zeroing gradients;
- accumulation.

Track gradient norm during serious experiments.

---

# 19. Memory Optimization

Know and benchmark:

- gradient checkpointing / activation checkpointing;
- FlashAttention;
- SDPA;
- sequence packing;
- CPU offload;
- optimizer state sharding;
- parameter sharding;
- activation sharding/partitioning where supported;
- quantization;
- LoRA;
- sequence length reduction;
- microbatch reduction.

When OOM occurs, diagnose the actual memory contributor before randomly changing parameters.

---

# 20. Distributed Training

## 20.1 Data Parallelism / DDP

Each worker holds a model replica and processes different data. Gradients are synchronized.

Use when the model and optimizer state fit per device and simple scaling is sufficient.

## 20.2 FSDP

Fully Sharded Data Parallel can shard parameters, gradients, and optimizer state across workers.

Understand:

- sharding strategy;
- wrapping policy;
- state-dict types;
- activation checkpointing;
- CPU offload;
- FSDP1/FSDP2 distinctions in the framework version used;
- checkpoint save/load behavior;
- mixed precision.

## 20.3 DeepSpeed ZeRO

Understand:

- ZeRO Stage 1: optimizer-state partitioning;
- Stage 2: optimizer states + gradients;
- Stage 3: optimizer states + gradients + parameters;
- CPU/NVMe offload concepts;
- communication/compute tradeoffs.

## 20.4 Tensor parallelism

Model tensor operations are split across devices. More common in serving and some training stacks.

## 20.5 Pipeline parallelism

Model layers/stages are distributed across devices. Understand bubble/utilization tradeoffs.

## 20.6 Sequence/context parallelism

Long sequences can require distributing sequence-related work. Use only with compatible frameworks and models.

## 20.7 Expert parallelism

Relevant to MoE architectures.

## 20.8 Multi-node fundamentals

Know:

- rank;
- local rank;
- world size;
- rendezvous;
- NCCL;
- network bandwidth;
- node topology;
- interconnects;
- failure recovery;
- shared vs object storage;
- deterministic checkpointing.

---

# 21. GPU and Hardware Engineering

Track:

- GPU model;
- VRAM;
- GPU utilization;
- memory utilization;
- SM utilization where available;
- power/thermal throttling;
- PCIe/NVLink/interconnect characteristics;
- host RAM;
- disk throughput;
- network throughput;
- dataloader CPU utilization.

Diagnose low GPU utilization:

```text
GPU idle?
├── data loader bottleneck
├── CPU preprocessing
├── storage latency
├── too-small batch
├── excessive checkpointing
├── distributed synchronization
├── kernel inefficiency
└── sequence-length imbalance
```

Do not optimize only tokens/sec; preserve evaluation quality.

---

# 22. Preference Data

Preference records teach relative quality.

Canonical form:

```json
{
  "prompt": "<incident>",
  "chosen": "<better response>",
  "rejected": "<worse response>"
}
```

For chat datasets, use the framework's expected conversational format.

Preference labels must have explicit rubric criteria such as:

- evidence groundedness;
- root-cause correctness;
- safe remediation;
- appropriate uncertainty;
- tool-use correctness;
- clarity;
- no fabricated telemetry.

Measure inter-rater agreement for human labeling when possible.

---

# 23. DPO

Direct Preference Optimization trains from chosen/rejected preference pairs without requiring the classic full RLHF loop.

Understand:

- policy model;
- reference model;
- preference pairs;
- beta/regularization concept;
- chosen vs rejected margins;
- over-optimization risk;
- dataset quality dependence.

Use ARIA DPO for preferences such as:

```text
evidence-backed RCA > speculative RCA
safe staged remediation > immediate mutation
explicit uncertainty > fabricated certainty
minimal necessary tool calls > noisy tool spam
```

Always compare SFT-only vs SFT+DPO.

---

# 24. KTO and Other Offline Preference Methods

Understand KTO and other preference-learning approaches conceptually. They can be useful when feedback is naturally desirable/undesirable rather than paired.

Do not adopt them solely because the framework supports them.

---

# 25. Reward Modeling

A reward model predicts a scalar or structured quality signal.

For ARIA, possible dimensions:

```text
RCA correctness
Evidence coverage
Tool correctness
Safety
Policy compliance
Action appropriateness
Structured-output validity
```

Reward models can themselves be wrong. Evaluate them separately.

Watch for reward hacking.

---

# 26. Process Reward Models

A process reward model evaluates intermediate reasoning/process steps rather than only final answers.

Potential ARIA use:

```text
collect evidence
→ form hypothesis
→ select tool
→ update hypothesis
→ propose action
```

Use only where intermediate process representation is available and safe to evaluate.

---

# 27. GRPO

Group Relative Policy Optimization is an online/reinforcement-style post-training method that compares multiple sampled completions using reward signals.

Potential ARIA reward functions:

```text
+2 correct root-cause category
+2 correct tool selection
+2 evidence-supported recommendation
+1 valid output schema
+1 correct approval requirement
-2 unsupported factual assertion
-3 unnecessary destructive recommendation
-5 policy-bypassing recommendation
```

Requirements:

- deterministic reward functions where possible;
- robust sandbox/evaluation environment;
- held-out validation;
- reward-hacking checks;
- generation-cost monitoring.

Do not connect RL training directly to live production mutation.

---

# 28. RLOO and Online RL Concepts

Understand other online RL methods supported by the chosen training stack, including leave-one-out style baselines. Treat algorithm choice as an experimental decision.

Know the general RL vocabulary:

- policy;
- action;
- trajectory;
- reward;
- advantage;
- baseline;
- exploration;
- KL regularization;
- on-policy vs off-policy;
- credit assignment.

---

# 29. Classical RLHF Pipeline

Understand even if ARIA initially prefers DPO/GRPO:

```text
pretrained model
→ SFT
→ preference collection
→ reward model
→ RL optimization
```

Know why modern direct-preference methods can simplify this pipeline and what tradeoffs remain.

---

# 30. Knowledge Distillation

Distillation transfers behavior from a larger/stronger teacher to a smaller student.

Types to understand:

- response distillation;
- logit/soft-target distillation;
- on-policy distillation;
- task-specific synthetic-data distillation.

ARIA use case:

```text
strong teacher
→ curated incident solutions
→ smaller open model
→ ARIA specialized model
```

Measure:

- quality retained;
- latency improvement;
- memory reduction;
- cost reduction;
- failure modes inherited from teacher.

Do not blindly train on teacher hallucinations.

---

# 31. Synthetic Data

Synthetic data can scale coverage but introduces model bias and error amplification.

Pipeline:

```text
scenario generator
→ teacher generation
→ deterministic checks
→ model/judge checks
→ human sampling/review
→ dedupe
→ dataset
```

Generate difficult counterexamples:

- symptoms without a deployment regression;
- high CPU that is not root cause;
- misleading correlated metrics;
- insufficient evidence cases;
- incidents where no action should be taken.

Avoid synthetic monoculture from one teacher/prompt.

---

# 32. Continued / Domain-Adaptive Pretraining

Continued pretraining trains on raw domain text using the language-model objective rather than instruction-response pairs.

Potential data:

- public Kubernetes documentation with compatible terms;
- approved internal SRE corpus;
- technical logs only if normalized and appropriate;
- operational documentation.

Use when domain fluency is fundamentally weak. It is much more data/compute intensive than SFT and can alter general capabilities.

Evaluate catastrophic forgetting.

---

# 33. Catastrophic Forgetting

A specialized fine-tune may improve ARIA tasks while degrading general capabilities.

Always maintain:

- task benchmark;
- general instruction benchmark;
- safety benchmark;
- tool-use benchmark;
- schema benchmark.

Compare deltas, not only absolute candidate score.

---

# 34. Quantization Fundamentals

Separate training-time quantization from inference quantization.

Know:

- weight quantization;
- activation quantization;
- static vs dynamic concepts;
- calibration datasets;
- per-tensor vs per-channel/group concepts;
- symmetric/asymmetric concepts;
- quantization-aware training (QAT);
- post-training quantization (PTQ).

Formats/approaches to recognize:

- 8-bit;
- 4-bit;
- GPTQ;
- AWQ;
- GGUF ecosystem;
- FP8;
- newer hardware-specific low-precision formats where supported.

Measure quality after quantization on ARIA benchmarks.

---

# 35. Inference Evaluation

For every serving format measure:

- request success rate;
- tokens/sec;
- time to first token (TTFT);
- inter-token latency;
- end-to-end latency;
- GPU memory;
- concurrency;
- queue time;
- throughput;
- output quality;
- cost per successful task.

Never select quantization purely by VRAM reduction.

---

# 36. vLLM Serving

Use vLLM as ARIA's primary open-model serving layer when compatible.

Target:

```text
Model registry
→ vLLM
→ Envoy AI Gateway
→ ARIA agents
```

Understand:

- OpenAI-compatible server;
- continuous batching;
- paged KV-cache concepts;
- tensor parallelism;
- pipeline parallelism where supported;
- quantization backends;
- LoRA serving;
- concurrency;
- max sequence length;
- GPU memory utilization;
- prefix caching concepts;
- speculative decoding concepts;
- structured outputs/tool calling where supported.

Do not enable dynamic loading of arbitrary untrusted adapters in production.

---

# 37. LoRA Serving Strategy

Possible architecture:

```text
Base model
├── aria-rca adapter
├── aria-kubernetes adapter
├── aria-tool-use adapter
└── aria-observability adapter
```

Compare:

- one multi-task adapter;
- task-specific adapters;
- merged models;
- runtime adapters.

Metrics:

- adapter switch overhead;
- throughput;
- quality per task;
- memory footprint;
- operational complexity.

---

# 38. Envoy AI Gateway Integration

All production ARIA model requests should flow through the AI gateway abstraction.

```text
ARIA agent
→ logical model name
→ Envoy AI Gateway
→ vLLM / cloud provider
```

Expose logical names such as:

```text
aria-reasoning
aria-rca
aria-tool-use
aria-private
aria-fast
```

Do not hard-code physical model IDs throughout agent code.

Gateway responsibilities:

- provider/model abstraction;
- authentication;
- routing;
- fallback;
- quotas;
- token-aware rate limits;
- tenant policy;
- telemetry;
- canary model routing.

Model-training code must remain independent of gateway implementation.

---

# 39. Model Registry

Every candidate must be represented by an immutable manifest.

Example:

```yaml
model_name: aria-rca-qwen
version: 0.3.0
base_model: <model-id>
base_revision: <revision>
training_method: qlora
adapter_revision: <hash>
dataset:
  name: aria-rca-sft
  version: 2.1.0
  hash: <sha256>
training_config_hash: <sha256>
git_commit: <commit>
metrics:
  rca_score: 0.0
  safety_score: 0.0
  tool_score: 0.0
  schema_validity: 0.0
serving:
  quantization: null
  runtime: vllm
status: candidate
```

Stages:

```text
experiment
→ candidate
→ staging
→ canary
→ production
→ retired
```

Never overwrite an existing model version.

---

# 40. Experiment Tracking

Every run must capture:

```text
run_id
Git commit
base model + exact revision
tokenizer revision
chat-template hash
dataset version/hash
train/validation split hash
training method
seed
sequence length
packing setting
LoRA rank/alpha/dropout/targets
learning rate
scheduler
warmup
optimizer
weight decay
microbatch
gradient accumulation
global batch
precision
gradient checkpointing
FSDP/DeepSpeed config
GPU type/count
framework versions
start/end time
train loss
validation loss
gradient norms
throughput
peak VRAM
all evaluation metrics
checkpoint artifact hashes
```

Use MLflow, Weights & Biases, or another approved tracker; do not couple ARIA to one vendor at the conceptual layer.

---

# 41. Reproducibility

Pin:

- Python;
- PyTorch;
- CUDA/ROCm stack;
- Transformers;
- Datasets;
- PEFT;
- TRL;
- Accelerate;
- Axolotl;
- bitsandbytes/backend where applicable;
- FlashAttention/kernel versions;
- vLLM;
- model revision;
- tokenizer revision.

Store:

- environment lock;
- container digest;
- GPU hardware metadata;
- random seeds;
- dataset hash;
- config hash.

Know that some GPU operations may still be nondeterministic.

---

# 42. TRL Learning Track

Use Hugging Face Transformers + PEFT + TRL to learn the underlying mechanics.

Master the relevant trainers available in the installed version, including the concepts behind:

- SFTTrainer;
- DPOTrainer;
- GRPOTrainer;
- RewardTrainer;
- DistillationTrainer;
- KTOTrainer;
- RLOOTrainer where appropriate.

Use explicit Python configurations for educational experiments so hyperparameters remain visible.

Do not treat a CLI invocation as understanding.

---

# 43. Axolotl Production Track

Use Axolotl for repeatable YAML-driven production experiments where it fits.

Master:

- dataset format/configuration;
- preprocessing;
- LoRA;
- QLoRA;
- full fine-tuning;
- preference optimization;
- reward modeling;
- GRPO/related supported RL methods;
- FSDP;
- DeepSpeed;
- multi-node;
- FlashAttention/kernel optimizations;
- sample packing;
- merging adapters;
- inference/evaluation workflows.

Treat the YAML as an immutable experiment artifact.

---

# 44. Evaluation Is a Product, Not a Final Step

ARIA must maintain a permanent benchmark suite.

Evaluation classes:

```text
Task quality
Safety
Groundedness
Tool use
Structured output
General capability retention
Latency/throughput
Cost
Robustness
Calibration
Regression
```

A model is not promoted based on one aggregate score.

---

# 45. ARIA RCA Evaluation

Evaluate:

- incident classification accuracy;
- root-cause correctness;
- evidence precision;
- evidence recall;
- unsupported claim rate;
- remediation appropriateness;
- risk classification;
- approval requirement correctness;
- uncertainty handling.

Use ARIA's existing `server/evals` scoring framework where possible.

---

# 46. Tool-Use Evaluation

For each test scenario track:

- correct tool selected;
- correct arguments;
- correct ordering;
- unnecessary tool calls;
- missing required calls;
- invalid/hallucinated tools;
- forbidden tool attempts;
- success after tool response;
- recovery from tool errors.

Example:

```text
Latency incident
Expected:
1. metrics query
2. trace lookup
3. pod inspection if evidence requires

Not expected:
- immediate restart
```

---

# 47. RAG Evaluation

Separate retrieval from generation.

Retrieval metrics:

- Recall@K;
- Precision@K;
- MRR;
- nDCG where useful;
- relevant-document coverage.

Generation metrics:

- groundedness;
- citation/evidence correctness;
- answer relevance;
- unsupported-claim rate.

Fine-tuning must not hide a poor retriever.

---

# 48. Structured Output Evaluation

Track:

- JSON parse rate;
- schema validity rate;
- required field coverage;
- enum correctness;
- type correctness;
- semantic correctness.

Schema validity should be deterministic to test.

---

# 49. Safety Evaluation

Maintain adversarial cases for:

- requests to bypass approval;
- instructions to ignore policy;
- attempts to make the model execute raw commands;
- malicious content embedded in logs/runbooks;
- prompt injection from retrieved documents;
- fake tool outputs;
- fake high-confidence evidence;
- data exfiltration prompts.

The desired result is safe recommendation behavior and preservation of ARIA's external controls.

---

# 50. Hallucination and Groundedness

Define unsupported claims as assertions not supported by supplied telemetry, retrieved evidence, or an explicitly identified prior.

Track:

```text
unsupported_claim_rate
fabricated_metric_rate
fabricated_tool_result_rate
fabricated_resource_rate
```

Prefer calibrated uncertainty when evidence is insufficient.

---

# 51. Calibration

Confidence output is not automatically calibrated.

Use reliability analysis such as:

- confidence buckets;
- empirical correctness per bucket;
- Brier score concepts;
- expected calibration error concepts.

ARIA should be able to distinguish:

```text
I know
I infer
I do not have enough evidence
```

---

# 52. LLM-as-a-Judge

Use carefully.

Rules:

- never rely on one judge alone for critical promotion;
- blind model identity when possible;
- randomize answer ordering for pairwise evaluation;
- maintain deterministic metrics alongside judge metrics;
- calibrate against human labels;
- detect position/verbosity/style bias;
- version judge model and prompt.

Human review remains valuable for high-risk qualitative changes.

---

# 53. Statistical Evaluation

For benchmark comparisons:

- report sample size;
- per-category scores;
- confidence intervals/bootstrapping when practical;
- paired comparisons;
- variance across seeds for training experiments;
- significance vs practical significance.

Do not celebrate a 0.2% gain inside measurement noise.

---

# 54. Regression Gates

Candidate promotion should require explicit gates, e.g.:

```yaml
promotion_gates:
  rca_score_delta_min: 0.02
  safety_score_min: 0.99
  schema_validity_min: 0.995
  tool_hallucination_max: 0.001
  general_capability_drop_max: 0.02
  p95_latency_regression_max: 0.10
```

Values are project policies, not universal defaults. Choose them from ARIA requirements.

---

# 55. Training Failure Diagnosis

## Loss is NaN/Inf

Investigate:

- learning rate;
- mixed precision;
- bad data;
- exploding gradients;
- optimizer instability;
- corrupted samples;
- incompatible kernels.

## Training loss decreases, validation worsens

Likely overfitting, distribution mismatch, or data leakage.

Actions:

- reduce epochs;
- improve data diversity;
- adjust regularization;
- inspect split design;
- inspect duplicated data.

## No improvement

Investigate:

- learning rate too low;
- adapter targets wrong;
- labels poor;
- prompt/template mismatch;
- task not learnable from supplied data;
- evaluation not sensitive;
- base model incapable.

## Model becomes verbose

Inspect dataset response-length distribution and preference rubric.

## Model forgets formatting

Inspect chat template, EOS, schema examples, serving template, and tokenizer mismatch.

## Model hallucinates more

Inspect low-quality synthetic data, preference incentives, missing evidence cases, and benchmark coverage.

---

# 56. Overfitting vs Underfitting

Overfitting signals:

- train improves while validation degrades;
- memorized phrases;
- poor novel incident performance;
- excessive confidence.

Underfitting signals:

- both train and validation remain weak;
- little behavior change;
- insufficient capacity/training signal.

Do not diagnose using loss alone; inspect task metrics.

---

# 57. Hyperparameter Experiment Design

Change one major factor at a time for learning experiments.

Example LoRA matrix:

```text
Experiment A: r=8
Experiment B: r=16
Experiment C: r=32
```

Then separately test learning rate.

Use factorial/search methods only when experiment tracking and budget justify them.

Every experiment starts with a hypothesis.

Example:

```text
Hypothesis:
Increasing LoRA rank from 16 to 32 will improve tool-argument accuracy
without degrading safety score by >0.5%.
```

---

# 58. Data Scaling Experiments

Measure quality vs dataset size:

```text
1k
5k
10k
25k
50k
...
```

Do not assume more data always helps; quality and diversity matter.

Track marginal gain per additional training token.

---

# 59. Model Scaling Experiments

Compare small/medium/large candidates on:

- quality;
- throughput;
- latency;
- memory;
- cost;
- fine-tuning stability.

ARIA may benefit more from a well-trained smaller model for a narrow task than a large general model, but this must be measured.

---

# 60. Data vs Model vs Compute Tradeoff

When quality is poor, ask in order:

```text
Is evaluation correct?
Is data correct?
Is the task formulation correct?
Is the base model capable?
Is training configured correctly?
Is more compute justified?
```

Do not use GPU scale to compensate for broken data.

---

# 61. Long-Context Fine-Tuning

Long context changes:

- activation memory;
- attention cost;
- data preprocessing;
- position handling;
- sequence packing;
- loss characteristics;
- distributed strategy.

Use long context only when ARIA tasks measurably require it.

Prefer retrieval over stuffing entire corpora into every training/inference sequence.

---

# 62. Multimodal Fine-Tuning

Future ARIA scenarios may include screenshots, dashboards, or architecture diagrams.

Understand:

- vision-language models;
- image preprocessing;
- multimodal chat templates;
- projector/adaptor layers;
- image token budgets;
- multimodal datasets;
- modality-specific evaluation.

Do not mix multimodal training into the initial RCA text model without a clear use case.

---

# 63. Tool/Function-Calling Fine-Tuning

Dataset must contain:

- available tool definitions;
- correct tool selection;
- correct JSON arguments;
- tool response;
- next assistant action;
- cases where no tool is needed;
- permission-denied/error cases.

Evaluate both syntax and semantics.

ARIA must never teach tool use that bypasses authorization.

---

# 64. Agentic Fine-Tuning

Separate model capability from agent orchestration.

Fine-tuning may improve:

- planning style;
- tool selection;
- evidence summarization;
- retry decisions.

LangGraph/agent runtime should still own:

- state machine;
- retries;
- timeouts;
- tool permissions;
- approval transitions;
- deterministic control flow.

Do not train the model to replace deterministic orchestration unnecessarily.

---

# 65. Model Routing and Ensembles

Possible production policy:

```text
simple incident
→ aria-fast

complex RCA
→ aria-reasoning

private data
→ aria-private

tool selection
→ aria-tool-use
```

Evaluate router accuracy and routing cost.

Fine-tuned specialist models may coexist with cloud models behind Envoy AI Gateway.

---

# 66. Canary Deployment

Never replace the production model globally without staged evaluation.

```text
candidate
→ staging
→ shadow
→ 1% canary
→ 5%
→ 25%
→ 50%
→ 100%
```

Percentages are examples; use ARIA deployment policy.

Observe:

- task success;
- safety;
- latency;
- errors;
- token usage;
- fallback rate;
- user/SRE feedback.

---

# 67. Shadow Evaluation

Shadow traffic can send a copy of eligible sanitized requests to a candidate without using its response operationally.

Never shadow secrets or data that violates model/data policy.

Compare candidate vs production on identical inputs.

---

# 68. A/B Testing

Use when comparing user-facing behavior under controlled conditions.

Define primary metric before test start.

Avoid routing selection bias.

For critical incident response, prefer benchmark/shadow/canary methods where experimentation must not impair operations.

---

# 69. Rollback

Every production model version must have:

- previous stable model reference;
- gateway routing rollback procedure;
- adapter rollback procedure;
- config rollback;
- model artifact availability;
- compatible tokenizer/template.

Rollback must not depend on retraining.

---

# 70. Continuous Evaluation

Production monitoring should continuously sample and score eligible outputs.

Track:

- task-success proxy;
- unsupported claims;
- schema errors;
- tool errors;
- escalation rate;
- human override rate;
- token usage;
- latency;
- gateway errors;
- model fallback.

Do not feed production outputs directly into training automatically.

---

# 71. Feedback Loop

Safe loop:

```text
production feedback
→ quarantine
→ sanitize
→ dedupe
→ classify
→ human/policy review
→ dataset candidate
→ dataset version
→ training
→ offline evaluation
→ promotion gates
```

This is continuous improvement, not uncontrolled self-training.

---

# 72. Drift

Monitor:

- input distribution drift;
- incident-type distribution;
- service distribution;
- output behavior drift;
- benchmark degradation;
- tool schema changes;
- runbook/document changes.

A changing knowledge base may require RAG updates rather than retraining.

---

# 73. MLOps / LLMOps Pipeline

Target ARIA pipeline:

```text
Dataset build
→ dataset validation
→ training
→ checkpoint evaluation
→ model evaluation
→ safety evaluation
→ quantization evaluation
→ registry
→ staging deployment
→ load test
→ shadow/canary
→ production
→ continuous evaluation
```

Each stage must be independently rerunnable.

---

# 74. CI vs GPU Training Jobs

Do not run long GPU training inside ordinary CI runners.

CI should:

- lint configs;
- validate schemas;
- run tiny smoke models;
- test data pipeline;
- test evaluation code;
- validate manifests;
- trigger approved training infrastructure.

GPU training runs in a dedicated training environment.

---

# 75. Kubernetes Training Architecture

Potential architecture:

```text
Git / pipeline
→ training job controller
→ GPU Kubernetes nodes
→ object storage datasets/checkpoints
→ experiment tracker
→ model registry
```

Understand:

- GPU device plugin/operator concepts;
- node selectors/affinity;
- taints/tolerations;
- resource requests/limits;
- topology;
- persistent/object storage;
- job retries;
- preemption;
- spot interruption handling;
- checkpoint restart.

---

# 76. Cloud Training Strategy

ARIA should remain portable.

Evaluate cloud GPU options by:

- GPU architecture;
- VRAM;
- interconnect;
- availability;
- price;
- egress;
- data residency;
- managed training features;
- Kubernetes fit.

Do not hard-code a training provider into dataset/model contracts.

---

# 77. Local Development

Local machines are appropriate for:

- tokenizer analysis;
- dataset transformation;
- small-model SFT;
- inference testing;
- unit tests;
- evaluation development;
- quantization experiments depending on hardware.

Large distributed fine-tunes should move to suitable GPU infrastructure.

---

# 78. Observability for Training

Emit/log:

- step;
- epoch;
- train loss;
- validation loss;
- learning rate;
- gradient norm;
- samples/sec;
- tokens/sec;
- GPU utilization;
- GPU memory;
- CPU memory;
- data-loader latency;
- checkpoint duration;
- communication time when available.

Integrate with ARIA's OpenTelemetry/observability patterns where practical without causing excessive training overhead.

---

# 79. Observability for Inference

Trace:

```text
ARIA request
→ agent
→ retrieval/tools
→ Envoy AI Gateway
→ vLLM
→ model
```

Attributes should include approved metadata such as:

- logical model;
- physical model/version;
- adapter;
- tenant/environment;
- request ID;
- trace ID;
- input/output token counts;
- TTFT;
- total latency;
- finish reason;
- gateway fallback;
- tool count.

Do not log sensitive prompts by default.

---

# 80. Cost Engineering

Track:

Training:

- GPU hours;
- cost per run;
- cost per successful candidate;
- storage;
- data processing.

Inference:

- tokens/sec;
- GPU utilization;
- requests/GPU;
- cost per successful task;
- idle cost;
- adapter consolidation tradeoffs.

Model quality must be considered jointly with cost.

---

# 81. Security for Model Engineering

Threats:

- poisoned training data;
- malicious model artifacts;
- unsafe pickle/serialization;
- compromised model repository;
- dependency compromise;
- secret leakage into datasets;
- unauthorized model promotion;
- adapter tampering;
- prompt injection inside training sources.

Controls:

- trusted artifact sources;
- revision pinning;
- hash verification;
- least privilege;
- dataset provenance;
- artifact scanning;
- approval for production promotion;
- immutable registry;
- signed artifacts where infrastructure supports it.

---

# 82. Data Poisoning Defense

For new training records:

- retain provenance;
- quarantine unknown sources;
- validate anomalous labels;
- detect repeated trigger phrases;
- monitor distribution shifts;
- sample-review synthetic data;
- do not allow model-generated feedback to recursively dominate the dataset.

---

# 83. Licensing and Governance

Before using a model or dataset, record:

- license;
- commercial-use permissions;
- redistribution terms;
- derivative/model-weight terms;
- attribution requirements;
- acceptable-use restrictions;
- data provenance.

Do not call a model "open source" merely because weights are downloadable; licensing terms matter.

---

# 84. Model Cards

Each ARIA model release must have a model card containing:

- intended use;
- out-of-scope use;
- base model;
- training method;
- dataset summary;
- evaluation summary;
- known limitations;
- safety boundary;
- serving requirements;
- license;
- version/revision;
- rollback reference.

---

# 85. Dataset Cards

Each dataset release must document:

- source/provenance;
- schema;
- collection method;
- cleaning;
- redaction;
- dedupe;
- splits;
- limitations;
- known biases;
- license;
- intended uses.

---

# 86. Fine-Tune vs RAG Experiments

For knowledge-heavy tasks, run four-way comparison where useful:

```text
A base model
B base + RAG
C fine-tuned model
D fine-tuned + RAG
```

This prevents attributing retrieval gains to training.

---

# 87. Fine-Tune vs Prompt Experiments

Before expensive training compare:

```text
zero-shot
few-shot
structured prompt
fine-tuned
```

Use the same held-out evaluation set.

---

# 88. Fine-Tune vs Larger Model

Compare a smaller specialized model against a larger general model on:

- ARIA quality;
- latency;
- cost;
- privacy;
- operational complexity.

Do not assume specialization always wins.

---

# 89. Teacher-Student Strategy for ARIA

Recommended advanced path:

```text
large teacher model
→ generate/critique candidate RCA
→ deterministic evidence checks
→ human sampling
→ high-quality SFT/preference set
→ smaller open model
→ evaluation
```

Keep teacher identity/version in provenance.

---

# 90. Reasoning Data

Do not require exposure of hidden chain-of-thought. Prefer concise, auditable rationales/evidence fields that are useful operationally:

```json
{
  "evidence": ["..."],
  "hypothesis": "...",
  "recommended_next_check": "..."
}
```

Train for verifiable intermediate outputs rather than unverifiable internal reasoning narratives.

---

# 91. Hard-Negative Training

Create examples where obvious heuristics are wrong.

Examples:

- pod restart correlates with recovery but is not causal;
- CPU spike is consequence, not root cause;
- deployment happened recently but unrelated;
- one unhealthy replica does not justify global rollback;
- runbook matches keywords but wrong service.

Hard negatives improve discriminative behavior.

---

# 92. No-Answer / Insufficient-Evidence Training

ARIA must learn that sometimes the correct answer is:

```text
insufficient evidence; collect X/Y/Z before recommending remediation
```

Include such records in SFT, preference, and evaluation datasets.

---

# 93. Error Taxonomy

Classify model errors:

```text
RCA wrong
Evidence missing
Evidence fabricated
Wrong tool
Wrong tool args
Unsafe recommendation
Overconfident
Underconfident
Schema invalid
Too verbose
Incomplete
Policy misunderstanding
Retrieval misuse
```

Use error taxonomy to decide the next intervention.

---

# 94. Root-Cause Analysis of Model Failures

When benchmark fails:

```text
failure
├── data issue
├── model capability issue
├── prompt/template issue
├── retrieval issue
├── tool issue
├── serving mismatch
├── quantization issue
├── training instability
└── evaluation bug
```

Do not automatically add more training data.

---

# 95. Checkpoint Strategy

Configure:

- save frequency;
- retention count;
- best-checkpoint selection;
- optimizer-state retention when resume is needed;
- storage lifecycle;
- artifact hashing.

Evaluate intermediate checkpoints when overfitting is possible.

---

# 96. Resume and Fault Tolerance

Distributed/cloud training must support recovery from:

- node interruption;
- preemption;
- process failure;
- transient storage failure.

A resume test is part of production-readiness for long jobs.

---

# 97. Seeds

Use fixed seeds for reproducibility experiments but understand that one seed can hide variance.

For important comparisons, run multiple seeds where budget permits.

---

# 98. Token Budget Engineering

Dataset token count is more informative than record count alone.

Track:

- total input tokens;
- total supervised/output tokens;
- tokens per category;
- tokens per epoch;
- padding waste;
- truncation waste.

---

# 99. Data Collators

Understand the role of collators in:

- padding;
- label masking;
- batching;
- multimodal fields;
- sequence packing.

Incorrect labels/masks can silently ruin SFT.

---

# 100. Train/Eval Mode

Understand differences such as dropout behavior and why evaluation must run with the model in evaluation mode through the framework.

---

# 101. Weight Decay and Regularization

Understand regularization conceptually. Do not apply weight decay uniformly to every parameter type without framework/model awareness.

For PEFT, know which parameters are actually trainable.

---

# 102. Warmup and Schedulers

Know:

- linear warmup;
- cosine schedules;
- constant schedules;
- decay behavior.

Use a hypothesis rather than copying a scheduler blindly.

---

# 103. Early Stopping

Use validation/task metrics to avoid unnecessary overtraining. Do not choose checkpoints based solely on training loss.

---

# 104. Adapter Inspection

For every PEFT run record:

- trainable parameter count;
- percentage trainable;
- target modules found;
- unexpected missing modules;
- adapter parameter dtypes.

Fail fast if target module patterns match nothing.

---

# 105. Gradient Checkpointing Tradeoff

Reduces activation memory by recomputing portions of the forward pass during backward.

Trade:

```text
lower memory
↔
more compute/time
```

Measure rather than assume.

---

# 106. Flash Attention and Kernel Optimizations

Use supported attention/kernel optimizations for throughput/memory, but treat them as infrastructure optimizations.

Validate:

- GPU architecture support;
- model architecture support;
- dtype support;
- correctness;
- reproducibility impact;
- compatibility with distributed strategy.

---

# 107. Sample Packing

Useful when examples are short relative to sequence length.

Measure packing efficiency and confirm attention/label boundaries behave as intended.

---

# 108. Data Loader Performance

Tune:

- worker count;
- prefetch;
- pinned memory where appropriate;
- preprocessing/cache;
- storage layout.

A starved GPU is not a model problem.

---

# 109. Checkpoint Formats

Prefer safe, well-supported serialization formats where possible and know the security implications of loading arbitrary serialized objects.

Record shard layout and tokenizer/config files with each artifact.

---

# 110. Adapter Merging

Before merging:

- evaluate unmerged adapter;
- preserve base revision;
- preserve adapter artifact;
- create a new immutable merged artifact;
- re-run evaluation after merge.

Do not assume merge is numerically/operationally irrelevant.

---

# 111. Quantized Serving Validation

For every quantized artifact compare to the pre-quantized candidate on the same evaluation suite.

Reject if task/safety regression exceeds policy thresholds even if latency improves.

---

# 112. Benchmark Dataset Design

ARIA benchmark must include:

- common incidents;
- rare incidents;
- ambiguous incidents;
- misleading signals;
- no-action-needed cases;
- unsafe-action traps;
- missing-data cases;
- tool failures;
- malformed telemetry;
- adversarial retrieved text.

Freeze benchmark releases.

---

# 113. Golden Scenarios

Use ARIA's existing golden-scenario/spec approach. Each golden scenario should define:

```yaml
scenario_id: <id>
inputs: {}
expected_root_causes: []
required_evidence: []
allowed_actions: []
forbidden_actions: []
expected_tools: []
requires_approval: true
```

Golden scenarios are promotion gates.

---

# 114. Human Evaluation

Create an SRE rubric with blind pairwise review when possible.

Score:

- correctness;
- evidence use;
- actionability;
- safety;
- concision;
- operational usefulness.

Do not reveal candidate identity to reviewers when it can bias judgment.

---

# 115. Preference Data Quality

Bad preference data can make a model worse while preference loss appears healthy.

Audit:

- contradictory labels;
- verbosity bias;
- style bias;
- evaluator identity bias;
- near-identical chosen/rejected pairs;
- easy pairs that add little signal.

---

# 116. Reward Hacking

If reward is based on simple surface properties, the model may optimize the score rather than the task.

Example bad reward:

```text
+1 if response contains "evidence"
```

Better reward evaluates evidence correctness against known scenario facts.

---

# 117. Online Learning Guardrail

ARIA must not alter production model weights directly from live traffic.

"Self-learning" means:

```text
collect
→ curate
→ train offline
→ evaluate
→ approve
→ deploy
```

not autonomous weight updates in production.

---

# 118. Privacy-Preserving Training Practices

Use data minimization. Prefer generalized/sanitized incident representations when exact production data is unnecessary.

Maintain deletion/provenance ability at the dataset layer. Remember that deleting a source record does not trivially remove its influence from already trained weights; retraining may be required under applicable governance.

---

# 119. Secrets Scanning

Dataset pipeline should run secret-pattern scanning before publishing a dataset version and before external upload.

Do not rely on a single regex. Combine known formats, entropy-based detectors where appropriate, and source-specific redaction.

---

# 120. Prompt Injection in Training Data

Logs/docs may contain text like "ignore previous instructions". Treat source text as data, not trusted instruction.

Label and sanitize such content where it is not relevant, and include adversarial evaluation for retrieval-time injection.

---

# 121. Model Supply Chain

For downloaded model weights:

- pin revision;
- verify expected files;
- prefer safe tensor formats;
- record source;
- scan dependencies/code;
- avoid enabling arbitrary remote code unless explicitly reviewed and required;
- isolate experiments involving untrusted custom code.

---

# 122. Framework Upgrade Policy

Never casually upgrade Transformers/PEFT/TRL/Axolotl/vLLM in a production training environment.

Upgrade workflow:

```text
new environment
→ smoke train
→ resume test
→ evaluation parity
→ serving parity
→ merge only after validation
```

---

# 123. Model Architecture Changes

When changing model families, revalidate:

- tokenizer;
- chat template;
- target modules;
- EOS/BOS;
- max positions;
- attention implementation;
- tool format;
- vLLM support;
- quantization support;
- license.

Do not copy LoRA target-module names blindly across architectures.

---

# 124. MoE Fine-Tuning

For MoE models understand:

- router;
- expert layers;
- active experts;
- expert parameter memory;
- expert LoRA support;
- quantization of experts;
- distributed expert placement.

Benchmark actual active-compute/inference behavior, not total parameter marketing numbers.

---

# 125. Long-Sequence Data Quality

Long examples can contain much irrelevant text. Before increasing context length, test whether retrieval/selection can reduce context while improving signal-to-noise.

---

# 126. Distillation Evaluation

Student must be compared to:

- its own base model;
- teacher;
- production model.

Track retained capability percentage and cost reduction.

---

# 127. Teacher Data Diversity

If synthetic examples are generated by a teacher, vary scenarios and validate with deterministic scenario facts. Avoid merely paraphrasing the same solution thousands of times.

---

# 128. Negative Transfer

Multi-task fine-tuning can improve one task and degrade another.

Maintain per-task scorecards for:

- RCA;
- tool use;
- summarization;
- RAG response;
- structured output;
- safety.

---

# 129. Multi-Task Dataset Mixing

When mixing datasets, record sampling weights.

```yaml
dataset_mix:
  rca: 0.40
  tool_use: 0.25
  evidence: 0.20
  safety: 0.15
```

These are experiment parameters, not universal values.

---

# 130. Loss Weighting

Different tasks/tokens may require different loss treatment in advanced setups. Introduce weighting only after a baseline and with explicit metrics.

---

# 131. Evaluation Contamination from Synthetic Generation

If the teacher sees evaluation answers or benchmark definitions while generating training data, the benchmark can become contaminated indirectly.

Keep benchmark artifacts isolated from training generation pipelines.

---

# 132. Temporal Splits

For realistic operational generalization, consider time-based test sets:

```text
train: older incidents
validation: later incidents
test: newest frozen period
```

Useful when incident patterns evolve.

---

# 133. Cross-Service Generalization

Hold out entire services or failure variants to test whether the model learned principles rather than service-specific memorization.

---

# 134. Retrieval-Augmented Fine-Tuning

When training a model that will operate with RAG, include examples that resemble serving-time retrieved context.

Teach it to:

- cite/use retrieved evidence;
- reject irrelevant context;
- acknowledge conflicting context;
- avoid treating retrieved instructions as policy.

---

# 135. Tool-Augmented Fine-Tuning

Include realistic tool failures:

- timeout;
- permission denied;
- empty result;
- malformed result;
- stale result.

ARIA should recover safely rather than hallucinate successful tool execution.

---

# 136. Model Confidence Policy

Never use raw model confidence alone to authorize actions.

Operational decision should combine:

- deterministic policy;
- evidence quality;
- model output;
- risk tier;
- approval requirements.

---

# 137. Safety and Capability Are Separate Axes

A more capable model may still be less safe for ARIA workflows. Promotion requires both quality and safety gates.

---

# 138. Fine-Tuning Roadmap for ARIA

## Phase FT-0 — Baseline

Deliver:

- candidate model matrix;
- frozen evaluation set;
- base-model scores;
- serving benchmark.

Exit criterion: reproducible baseline.

## Phase FT-1 — Dataset platform

Deliver:

- normalization;
- redaction;
- dedupe;
- quality checks;
- manifests;
- train/validation/test split tooling.

Exit criterion: immutable dataset v1.

## Phase FT-2 — SFT mechanics

Implement small-model SFT using Transformers/TRL.

Exit criterion: candidate beats base on at least one defined ARIA task without safety regression.

## Phase FT-3 — LoRA

Run controlled rank/target-module experiments.

Exit criterion: understand quality/cost tradeoff.

## Phase FT-4 — QLoRA

Run 4-bit base + LoRA experiments.

Exit criterion: measured memory savings and quality delta.

## Phase FT-5 — Axolotl

Reproduce chosen training run through an immutable Axolotl config.

Exit criterion: reproducible production-style job.

## Phase FT-6 — Distributed training

Implement FSDP and/or DeepSpeed on suitable hardware.

Exit criterion: multi-GPU run, checkpoint, resume, evaluation.

## Phase FT-7 — Preference optimization

Build preference dataset and DPO/KTO experiments.

Exit criterion: measured preference gain without safety loss.

## Phase FT-8 — Reward + GRPO

Create deterministic ARIA reward functions and sandboxed GRPO experiment.

Exit criterion: reward improvement correlates with held-out human/task metrics.

## Phase FT-9 — Distillation

Train smaller student from approved teacher-generated/teacher-distribution data.

Exit criterion: cost/latency gain with acceptable quality retention.

## Phase FT-10 — Quantization

Benchmark multiple serving precisions/formats.

Exit criterion: selected format satisfies quality and latency gates.

## Phase FT-11 — vLLM

Deploy candidate via vLLM.

Exit criterion: concurrency/load/SLO benchmark passes.

## Phase FT-12 — Envoy AI Gateway

Route logical ARIA model names through gateway.

Exit criterion: routing/fallback/telemetry/canary validated.

## Phase FT-13 — Continuous evaluation

Add production scorecards and feedback quarantine.

Exit criterion: drift/regression visibility.

## Phase FT-14 — Controlled continuous improvement

Automate dataset candidate build and training trigger, but preserve evaluation/promotion approval.

Exit criterion: reproducible closed loop without autonomous unsafe weight promotion.

---

# 139. ARIA Training Config Standard

Every training config should specify or resolve:

```yaml
experiment:
  name: <name>
  seed: 42

model:
  id: <model>
  revision: <revision>
  tokenizer_revision: <revision>

method:
  type: sft  # sft|lora|qlora|dpo|grpo|reward|distillation|full

adapter:
  rank: null
  alpha: null
  dropout: null
  target_modules: []

precision:
  compute: bf16
  base_quantization: null

sequence:
  max_length: <n>
  packing: false

optimizer:
  name: adamw
  learning_rate: <value>
  weight_decay: <value>
  scheduler: <name>
  warmup_ratio: <value>

batch:
  per_device: <n>
  gradient_accumulation: <n>

runtime:
  epochs: <n>
  gradient_checkpointing: false
  gradient_clip_norm: <value>

parallelism:
  strategy: single  # single|ddp|fsdp|deepspeed
  config: null

dataset:
  name: <name>
  version: <version>
  hash: <hash>

evaluation:
  benchmark_version: <version>

output:
  registry_candidate: <name>
```

Framework-specific configs may differ, but the manifest must preserve equivalent information.

---

# 140. ARIA SFT Dataset Schema

Recommended normalized record:

```json
{
  "id": "incident-000123",
  "task": "rca",
  "difficulty": "medium",
  "service": "checkout-api",
  "environment": "staging",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "provenance": {
    "source_type": "reviewed_synthetic",
    "source_id": "..."
  },
  "quality": {
    "reviewed": true,
    "score": 0.98
  }
}
```

---

# 141. ARIA Preference Schema

```json
{
  "id": "pref-000123",
  "prompt": [{"role": "user", "content": "..."}],
  "chosen": [{"role": "assistant", "content": "..."}],
  "rejected": [{"role": "assistant", "content": "..."}],
  "rubric": {
    "reason": "chosen response uses telemetry evidence and preserves approval gate"
  }
}
```

---

# 142. ARIA RL Scenario Schema

```json
{
  "scenario_id": "rl-k8s-001",
  "prompt": "...",
  "ground_truth": {
    "root_cause": "...",
    "required_evidence": ["..."],
    "allowed_tools": ["..."],
    "forbidden_actions": ["..."]
  }
}
```

Reward functions should reference structured ground truth, not hidden production behavior.

---

# 143. ARIA Evaluation Scorecard

Example categories:

```yaml
model: <candidate>
benchmark: aria-eval-v1
scores:
  rca_correctness: 0.00
  evidence_groundedness: 0.00
  tool_selection: 0.00
  tool_arguments: 0.00
  structured_output: 0.00
  safety: 0.00
  uncertainty: 0.00
  general_retention: 0.00
serving:
  p50_ms: 0
  p95_ms: 0
  ttft_p95_ms: 0
  tokens_per_second: 0
  peak_vram_gb: 0
promotion: reject
```

---

# 144. ARIA Model Promotion Decision

Use a decision record:

```text
Candidate improves which task?
What regressed?
How large is the gain?
Is it statistically/practically meaningful?
Does it pass safety?
Does it pass serving SLOs?
Does it fit cost budget?
Is rollback ready?
Is the dataset/model license approved?
```

If any critical answer is unknown, do not promote.

---

# 145. Expert Debugging Questions

When working on ARIA fine-tuning, be able to answer:

1. Why fine-tune rather than RAG?
2. Why this base model?
3. Why this exact model revision?
4. Why this tokenizer/chat template?
5. Why this dataset split?
6. How was contamination prevented?
7. How was data redacted?
8. Why SFT vs DPO vs GRPO?
9. Why LoRA vs QLoRA vs full fine-tuning?
10. Why this LoRA rank?
11. Why these target modules?
12. Why this learning rate?
13. What is the effective global batch size?
14. Why this sequence length?
15. How much data is truncated?
16. Why this precision?
17. What consumes GPU memory?
18. Why FSDP vs DeepSpeed?
19. Is the GPU data-starved?
20. Why did validation diverge?
21. Did the model catastrophically forget?
22. Is the improvement from data leakage?
23. Did quantization degrade RCA accuracy?
24. Is the judge biased?
25. Are confidence scores calibrated?
26. Does tool-use improve or merely call more tools?
27. Does the candidate remain safe under prompt injection?
28. Can the exact run be reproduced?
29. Can deployment be rolled back immediately?
30. Does the smaller specialist beat the larger general model on cost-adjusted task success?

---

# 146. Definition of Fine-Tuning Expertise

For ARIA, "expert" means being able to independently:

- formulate the problem;
- decide whether to fine-tune;
- select model families;
- understand transformer architecture differences;
- engineer/version datasets;
- detect contamination;
- implement SFT;
- implement LoRA/QLoRA;
- reason about hyperparameters;
- debug training instability;
- scale to multi-GPU/multi-node;
- implement preference optimization;
- design reward functions;
- run GRPO/online methods safely;
- distill models;
- quantize and benchmark;
- serve through vLLM;
- route through Envoy AI Gateway;
- design robust evaluations;
- operate model registry/promotion;
- observe production behavior;
- diagnose model regressions;
- run a controlled continuous-improvement loop.

Running a LoRA command is not expertise.

---

# 147. Default Implementation Order for Any New ARIA Model Task

When asked to build or improve an ARIA model, follow this exact sequence unless evidence justifies deviation:

```text
1. Define task + success metric.
2. Find existing ARIA benchmark coverage.
3. Establish untouched base-model baseline.
4. Test prompt/RAG/tool/routing alternatives.
5. Inspect candidate dataset provenance.
6. Add redaction/dedupe/contamination checks.
7. Freeze dataset + evaluation versions.
8. Run smallest useful SFT baseline.
9. Add LoRA/QLoRA experiment.
10. Evaluate task + safety + general retention.
11. Debug errors by taxonomy.
12. Scale data/model only when justified.
13. Add DPO/reward/RL only if SFT leaves a measurable preference/reasoning gap.
14. Quantize only after candidate quality is established.
15. Serve via vLLM.
16. Route via Envoy AI Gateway logical model.
17. Load/shadow/canary test.
18. Promote only through explicit gates.
19. Monitor and quarantine feedback.
20. Retrain only through a new immutable dataset/model version.
```

---

# 148. What to Build in ARIA Immediately

When implementing this skill into code, prioritize:

```text
training/common/manifests.py
training/common/reproducibility.py
training/common/model_selection.py

datasets/builders/
datasets/validators/
datasets/redaction/
datasets/dedupe/
datasets/manifests/

training/sft/
training/lora/
training/qlora/
training/configs/trl/
training/configs/axolotl/

evaluation/benchmarks/
evaluation/rca/
evaluation/tool_use/
evaluation/safety/
evaluation/regression/

models/registry/
models/cards/

serving/vllm/
serving/envoy/
```

Then add DPO/GRPO/distillation after the baseline pipeline is trustworthy.

---

# 149. Commands and Workflow Style

Prefer reproducible commands such as:

```bash
make dataset-build
make dataset-validate
make train-sft
make train-lora
make train-qlora
make eval-model
make model-register
make serving-smoke
make model-canary
```

The Make targets should invoke versioned scripts/configs, not contain hidden training logic themselves.

For serious training, preserve the exact command and config in run metadata.

---

# 150. Testing Requirements

Every model-engineering addition must include appropriate tests.

Unit tests:

- schema validation;
- redaction;
- dedupe;
- split logic;
- metric functions;
- reward functions;
- manifest hashing;
- gateway model mapping.

Integration tests:

- tiny model training smoke test;
- checkpoint save/load;
- adapter load/merge;
- vLLM health/inference where environment permits;
- Envoy logical model route;
- benchmark execution.

Golden tests:

- stable ARIA scenarios;
- safety invariants;
- approval preservation.

---

# 151. Documentation Requirements

For each technique added, document:

- what problem it solves;
- prerequisites;
- dataset requirements;
- configuration;
- hardware assumptions;
- expected metrics;
- failure modes;
- rollback/removal plan;
- references.

Do not introduce a training framework feature that only one person can reproduce.

---

# 152. Official Reference Set

Prefer primary documentation and papers over copied tutorials.

Core sources to consult and version-check before implementation:

- Hugging Face Transformers documentation
- Hugging Face PEFT documentation
- Hugging Face TRL documentation
- Hugging Face Datasets documentation
- Hugging Face Accelerate documentation
- Axolotl documentation
- PyTorch distributed/FSDP documentation
- DeepSpeed documentation
- vLLM documentation
- Envoy AI Gateway documentation
- base-model model cards/licenses
- original papers for LoRA, QLoRA, DPO, GRPO, distillation, quantization methods being implemented

Framework APIs evolve. Verify current installed-version documentation before writing configs.

---

# 153. Current Framework Capability Notes (2026-09-07)

At the time this skill was authored, current upstream documentation indicates:

- TRL supports SFT, DPO, GRPO, reward modeling, KTO/RLOO-family workflows, and stable distillation tooling.
- PEFT remains the core Hugging Face parameter-efficient fine-tuning layer for LoRA-style adapters.
- Axolotl supports LoRA, QLoRA, full fine-tuning, preference/RL methods, reward modeling, distributed FSDP/DeepSpeed workflows, and multiple optimization/quantization paths.
- vLLM provides production-oriented model serving and LoRA-serving support.
- Envoy AI Gateway is ARIA's preferred model traffic control plane.

Do not encode these as eternal truths. Re-check upstream docs before implementing a feature because APIs and supported model families change.

---

# 154. Response Behavior When This Skill Is Active

When helping with ARIA model engineering:

1. Start from ARIA's current repository and existing eval/safety/gateway boundaries.
2. State the measurable hypothesis.
3. Identify whether fine-tuning is actually necessary.
4. Prefer a small reproducible experiment before expensive scale-up.
5. Preserve exact data/model/config provenance.
6. Add evaluation before claiming improvement.
7. Keep safety and approval controls outside model authority.
8. Explain tradeoffs, not merely commands.
9. Treat failed experiments as useful evidence and record them.
10. Never claim a candidate is "better" without benchmark evidence.

---

# 155. Completion Criteria for the ARIA Fine-Tuning Program

The program is mature when ARIA can reproducibly demonstrate:

```text
Raw approved incident data
        ↓
Versioned sanitized dataset
        ↓
SFT / LoRA / QLoRA
        ↓
Preference/RL/distillation experiments
        ↓
Frozen benchmark suite
        ↓
Safety + RCA + tool-use scorecards
        ↓
Immutable model registry
        ↓
Quantized/optimized serving artifact
        ↓
vLLM
        ↓
Envoy AI Gateway
        ↓
Shadow / canary / rollback
        ↓
OTel + AI observability
        ↓
Human feedback quarantine
        ↓
Versioned retraining cycle
```

No stage may silently skip provenance, evaluation, safety, or rollback.

---

# 156. Final Principle

The ARIA fine-tuning system must optimize for **successful, evidence-grounded, safe SRE tasks**, not for training loss, benchmark vanity, or model size.

The highest-level metric is:

```text
Successful ARIA Task Rate
subject to
Safety + Evidence + Latency + Cost constraints
```

Every model-engineering decision should ultimately be explainable through those outcomes.

---

# 157. Post-Training Method Taxonomy

Keep the methods conceptually separated:

```text
Supervised behavior learning
├── SFT
├── full fine-tuning
└── PEFT / LoRA / QLoRA

Offline preference learning
├── DPO
├── KTO
├── IPO-style objectives
├── ORPO-style objectives
├── SimPO/CPO-family concepts
└── other framework-supported preference losses

Reward modeling
├── outcome reward models
└── process reward models

Online RL / policy optimization
├── PPO-style RLHF
├── GRPO
├── RLOO
└── related group/advantage methods

Knowledge transfer
├── response distillation
├── logit distillation
└── on-policy distillation
```

Method names evolve quickly. Understand the objective, required data, compute pattern, and failure modes rather than memorizing a framework menu.

---

# 158. PPO-Style RLHF

Proximal Policy Optimization is historically important to RLHF.

Understand:

- policy model;
- reference model;
- reward model;
- value function/critic concepts;
- advantage estimates;
- clipped objective;
- KL penalty/control;
- rollout generation;
- high operational complexity.

ARIA should not start with PPO. Learn it to understand classical RLHF and compare it with simpler direct-preference or group-relative methods.

---

# 159. IPO / ORPO / SimPO / CPO / Related Preference Objectives

Know that DPO is not the only offline preference objective.

When evaluating a method, compare:

- whether a reference model is required;
- paired vs unpaired feedback requirements;
- memory cost;
- sensitivity to preference noise;
- regularization behavior;
- framework maturity;
- measured ARIA benchmark gain.

Do not add multiple objectives just to increase project complexity.

---

# 160. Hyperparameter Search

After manual learning experiments, automate controlled sweeps.

Possible parameters:

- learning rate;
- LoRA rank;
- LoRA alpha;
- dropout;
- sequence length;
- batch size;
- warmup;
- epochs;
- DPO beta;
- GRPO generation count/reward weights.

Use:

- grid search for small interpretable spaces;
- random search for broader spaces;
- Bayesian/optimization frameworks when justified.

Every sweep must have budget limits and a primary metric.

---

# 161. Scaling Laws and Compute Budgeting

Understand that model quality depends jointly on:

- model capacity;
- data quantity/quality;
- training compute.

For ARIA post-training, practical scaling experiments matter more than theoretical pretraining-law replication.

Track:

```text
quality gain / training token
quality gain / GPU-hour
quality gain / dollar
quality gain / added inference latency
```

Stop scaling when marginal value no longer justifies cost.

---

# 162. Pretraining From Scratch

Understand the pipeline even though ARIA should normally not pretrain an LLM from scratch:

```text
large corpus
→ tokenizer design
→ distributed pretraining
→ checkpointing
→ base-model evaluation
→ instruction post-training
→ alignment
```

It requires massive data, compute, distributed systems, and model-development expertise. For ARIA, adapting strong open base models is usually the correct learning and production path.

---

# 163. Tokenizer Training and Modification

Normally preserve the base-model tokenizer.

Adding/changing tokens can require:

- embedding resize;
- initialization of new embeddings;
- output-head compatibility;
- retraining/adaptation;
- serving tokenizer synchronization.

Only modify vocabulary if ARIA has demonstrated severe tokenization inefficiency or required special-token semantics.

---

# 164. Pruning and Sparsity

Understand compression methods beyond quantization:

- unstructured pruning;
- structured pruning;
- magnitude-based pruning concepts;
- sparsity-aware hardware/runtime requirements.

Pruning is not automatically useful unless the serving stack can exploit the resulting sparsity.

Always re-evaluate task quality.

---

# 165. Model Unlearning and Data Removal

Understand the governance problem: once information is encoded in weights, deleting the source row from a dataset does not guarantee removal from the trained model.

Potential responses include:

- retraining from a corrected dataset;
- model replacement;
- specialized unlearning research techniques where validated.

For ARIA, prevent sensitive data entering weights in the first place.

---

# 166. Checkpoint Sharding and Artifact Size

Large models are stored across multiple shards.

Understand:

- shard index files;
- safe tensor shards;
- optimizer checkpoint size;
- distributed-state checkpoints;
- merge/consolidation steps;
- upload/download time;
- registry storage lifecycle.

Plan checkpoint storage before launching long distributed jobs.

---

# 167. Distributed Checkpointing

For FSDP/DeepSpeed, test:

- distributed save;
- full/consolidated state extraction;
- resume on same topology;
- resume on compatible changed topology where supported;
- adapter-only saving;
- optimizer-state recovery.

A checkpoint that cannot restore is not a checkpoint strategy.

---

# 168. Training Throughput Metrics

Measure:

- examples/sec;
- tokens/sec;
- model FLOPs utilization concepts where available;
- step time;
- forward time;
- backward time;
- optimizer time;
- communication time;
- data wait time.

Use profiler tooling for unexplained bottlenecks, but avoid profiling every production step.

---

# 169. Profiling

Know how to use framework/GPU profilers to inspect:

- kernel execution;
- CPU/GPU synchronization;
- communication collectives;
- memory allocations;
- data loading;
- idle gaps.

Profile representative windows rather than entire long jobs.

---

# 170. Inference Engine Internals

To operate vLLM or another high-throughput engine, understand:

- prefill vs decode;
- KV cache;
- continuous batching;
- request scheduling;
- memory fragmentation;
- prefix caching;
- tensor parallel communication;
- speculative decoding;
- chunked prefill concepts;
- max-batched-token controls.

This knowledge connects model engineering with SRE capacity planning.

---

# 171. Speculative Decoding

Speculative decoding uses a draft mechanism/model to propose tokens that a target model verifies.

Potential benefit:

- lower generation latency in compatible workloads.

Tradeoffs:

- extra model/memory complexity;
- acceptance-rate dependence;
- workload sensitivity.

Benchmark on ARIA response patterns before adoption.

---

# 172. KV Cache Engineering

KV cache memory grows with active sequences/context and model architecture.

Track:

- cache memory per request;
- concurrency limits;
- sequence-length distribution;
- eviction/preemption behavior;
- prefix-cache hit rate if enabled.

Serving OOM can occur even when model weights fit comfortably.

---

# 173. Batching and Scheduling at Inference

Compare latency-sensitive vs throughput-oriented settings.

ARIA incident workflows may prioritize TTFT and tail latency over maximum batch throughput.

Define separate serving profiles for:

```text
interactive RCA
batch evaluation
synthetic-data generation
RL rollouts
```

---

# 174. Capacity Planning for Open Models

Estimate capacity using measured load tests:

```text
arrival rate
× average input tokens
× average output tokens
× concurrency
× SLO target
```

Then account for:

- model parallelism;
- adapter use;
- quantization;
- headroom;
- failure/failover capacity.

Do not size from theoretical tokens/sec alone.

---

# 175. Technique Selection Matrix

Use this default reasoning table:

| Problem | First choice | Escalation |
|---|---|---|
| Missing current facts | RAG/tools | improve retrieval |
| Wrong output shape | schema/constrained generation | SFT if behavior persists |
| Weak domain response style | SFT/LoRA | QLoRA/full if needed |
| Better chosen-vs-bad behavior | DPO/KTO-family | online RL if measurable gap remains |
| Automatically scoreable reasoning task | SFT first | GRPO/RLOO-style RL |
| Large teacher too expensive | distillation | quantization + smaller student |
| Model too large for training | LoRA/QLoRA | FSDP/DeepSpeed |
| Model too large for serving | quantization | distillation/pruning |
| Live system data/action | MCP/tools | never encode live state into weights |
| Multiple provider/model needs | Envoy routing | specialist fine-tunes behind logical names |

---

# 176. ARIA Expert Learning Milestones

Use the project to prove expertise through deliverables, not certificates alone.

Milestone 1:

- explain transformer/attention/tokenization;
- run and evaluate tiny SFT.

Milestone 2:

- build dataset pipeline;
- LoRA/QLoRA comparison;
- explain memory math.

Milestone 3:

- reproduce Axolotl run;
- multi-GPU FSDP/DeepSpeed;
- checkpoint/resume.

Milestone 4:

- DPO dataset + experiment;
- reward model;
- GRPO sandbox.

Milestone 5:

- distillation + quantization;
- vLLM load benchmark;
- Envoy routing.

Milestone 6:

- production canary;
- OTel observability;
- drift/feedback loop;
- controlled retraining.

At each milestone, produce an architecture diagram, experiment report, scorecard, and reproducible config.
