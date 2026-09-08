from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import Any

import yaml

from training.common.data_pipeline import read_jsonl, validate_built_dataset


def load_config(path: str | Path) -> dict[str, Any]:
    config = yaml.safe_load(Path(path).read_text())
    required = ("experiment", "model", "method", "dataset", "output")
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"training config missing sections: {', '.join(missing)}")
    if config["method"]["type"] not in {"sft", "lora", "qlora"}:
        raise ValueError("method.type must be sft, lora, or qlora")
    return config


def build_plan(config: dict[str, Any]) -> dict[str, Any]:
    manifest = validate_built_dataset(config["dataset"]["manifest"])
    return {
        "experiment": config["experiment"]["name"],
        "seed": config["experiment"].get("seed", 42),
        "model": config["model"],
        "method": config["method"]["type"],
        "dataset": {"name": manifest.name, "version": manifest.version, "sha256": manifest.source_sha256},
        "train_records": manifest.split_counts["train"],
        "validation_records": manifest.split_counts["validation"],
        "output": config["output"]["directory"],
    }


def _precision_dtype(torch: Any, value: str) -> Any:
    return {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}[value]


def train(config: dict[str, Any]) -> dict[str, Any]:
    cache_dir = str(Path(config["model"].get("cache_dir", "artifacts/cache/huggingface")).resolve())
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = cache_dir
    os.environ["HF_HUB_CACHE"] = str(Path(cache_dir) / "hub")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    try:
        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    except ImportError as exc:
        raise RuntimeError("Install requirements-training.txt; QLoRA also requires requirements-training-cuda.txt") from exc

    plan = build_plan(config)
    seed = int(plan["seed"])
    random.seed(seed)
    torch.manual_seed(seed)
    model_id = config["model"]["id"]
    revision = config["model"].get("revision")
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, cache_dir=cache_dir)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    method = config["method"]["type"]
    precision = config.get("precision", {}).get("compute", "fp32")
    model_kwargs: dict[str, Any] = {
        "revision": revision,
        "cache_dir": cache_dir,
        "torch_dtype": _precision_dtype(torch, precision),
    }
    if method == "qlora":
        if not torch.cuda.is_available():
            raise RuntimeError("QLoRA requires a supported CUDA GPU; use the LoRA local config on this machine")
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=config["precision"].get("base_quantization", "nf4"),
            bnb_4bit_compute_dtype=_precision_dtype(torch, precision),
        )
        model_kwargs["device_map"] = "auto"
    model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
    if method in {"lora", "qlora"}:
        if method == "qlora":
            model = prepare_model_for_kbit_training(model)
        adapter = config["adapter"]
        model = get_peft_model(model, LoraConfig(
            r=int(adapter["rank"]),
            lora_alpha=int(adapter["alpha"]),
            lora_dropout=float(adapter.get("dropout", 0.0)),
            target_modules=adapter["target_modules"],
            task_type="CAUSAL_LM",
        ))
    if bool(config["runtime"].get("gradient_checkpointing", False)):
        model.config.use_cache = False
        if method in {"lora", "qlora"}:
            model.enable_input_require_grads()

    class TokenizedChatDataset(torch.utils.data.Dataset):
        def __init__(self, records: list[dict[str, Any]]):
            self.items: list[dict[str, Any]] = []
            for record in records:
                text = tokenizer.apply_chat_template(record["messages"], tokenize=False, add_generation_prompt=False)
                self.items.append(tokenizer(text, truncation=True, max_length=int(config["sequence"]["max_length"])))

        def __len__(self) -> int:
            return len(self.items)

        def __getitem__(self, index: int) -> dict[str, Any]:
            return self.items[index]

    train_dataset = TokenizedChatDataset(read_jsonl(config["dataset"]["train"]))
    validation_dataset = TokenizedChatDataset(read_jsonl(config["dataset"]["validation"]))
    output = config["output"]["directory"]
    runtime = config["runtime"]
    batch = config["batch"]
    optimizer = config["optimizer"]
    args = TrainingArguments(
        output_dir=output,
        num_train_epochs=float(runtime["epochs"]),
        per_device_train_batch_size=int(batch["per_device"]),
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=int(batch["gradient_accumulation"]),
        learning_rate=float(optimizer["learning_rate"]),
        weight_decay=float(optimizer.get("weight_decay", 0.0)),
        warmup_ratio=float(optimizer.get("warmup_ratio", 0.0)),
        gradient_checkpointing=bool(runtime.get("gradient_checkpointing", False)),
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=1,
        report_to=[],
        seed=seed,
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    result = trainer.train()
    trainer.save_model(output)
    tokenizer.save_pretrained(output)
    Path(output, "training-plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    response = {**plan, "train_metrics": result.metrics}
    tracking = config.get("tracking", {})
    if tracking.get("enabled", False):
        try:
            import mlflow
        except ImportError as exc:
            raise RuntimeError("MLflow tracking is enabled but mlflow is not installed") from exc
        tracking_uri = Path(tracking.get("uri", "artifacts/mlruns")).resolve().as_uri()
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(tracking.get("experiment", "aria-open-model-finetuning"))
        with mlflow.start_run(run_name=config["experiment"]["name"]) as run:
            mlflow.log_params({
                "model_id": model_id,
                "model_revision": revision or "default",
                "method": method,
                "dataset_name": plan["dataset"]["name"],
                "dataset_version": plan["dataset"]["version"],
                "dataset_sha256": plan["dataset"]["sha256"],
                "seed": seed,
            })
            mlflow.log_metrics({key: float(value) for key, value in result.metrics.items() if isinstance(value, (int, float))})
            mlflow.log_artifacts(output, artifact_path="model")
            response["mlflow_run_id"] = run.info.run_id
    return response


def main() -> None:
    parser = argparse.ArgumentParser(description="ARIA reproducible SFT/LoRA/QLoRA runner")
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    print(json.dumps(build_plan(config) if args.dry_run else train(config), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
