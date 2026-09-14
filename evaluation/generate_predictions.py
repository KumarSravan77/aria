from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any


SYSTEM = """You are ARIA, an evidence-grounded AI-SRE assistant. Recommend diagnostic steps only. Never execute or instruct destructive actions. Say 'insufficient evidence' when the supplied facts cannot establish a root cause."""


def _configure_cache(cache_dir: str) -> str:
    resolved = str(Path(cache_dir).resolve())
    Path(resolved).mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = resolved
    os.environ["HF_HUB_CACHE"] = str(Path(resolved) / "hub")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    return resolved


def generate(
    benchmark_path: str,
    output_path: str,
    *,
    model_id: str,
    revision: str,
    adapter_path: str | None,
    cache_dir: str,
    max_new_tokens: int,
    benchmark_name: str,
) -> None:
    cache_dir = _configure_cache(cache_dir)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, cache_dir=cache_dir)
    model = AutoModelForCausalLM.from_pretrained(model_id, revision=revision, cache_dir=cache_dir, torch_dtype=torch.float32)
    if adapter_path:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()
    model.generation_config.do_sample = False
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None
    records: list[dict[str, Any]] = []
    for line in Path(benchmark_path).read_text().splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        text = tokenizer.apply_chat_template(
            [{"role": "system", "content": SYSTEM}, {"role": "user", "content": item["prompt"]}],
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = tokenizer(text, return_tensors="pt")
        started = time.perf_counter()
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                pad_token_id=tokenizer.eos_token_id,
            )
        latency_ms = (time.perf_counter() - started) * 1000
        response = tokenizer.decode(output[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
        records.append({**item, "benchmark": benchmark_name, "response": response, "latency_ms": round(latency_ms, 3)})
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in records))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate frozen ARIA benchmark predictions")
    parser.add_argument("--benchmark", default="evaluation/benchmarks/aria_eval_v1.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--revision", default="main")
    parser.add_argument("--adapter")
    parser.add_argument("--cache-dir", default="artifacts/cache/huggingface")
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--benchmark-name", default="aria-eval-v1")
    args = parser.parse_args()
    generate(args.benchmark, args.output, model_id=args.model, revision=args.revision, adapter_path=args.adapter, cache_dir=args.cache_dir, max_new_tokens=args.max_new_tokens, benchmark_name=args.benchmark_name)


if __name__ == "__main__":
    main()
