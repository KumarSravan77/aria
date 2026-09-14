from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from evaluation.model_scorecard import evaluate_file
from models.registry.local_registry import register_model
from models.registry.promotion import compare_for_promotion, evaluate_promotion
from training.common.data_pipeline import build_dataset, validate_built_dataset
from training.common.data_quality import audit_dataset, enforce_audit


def main() -> None:
    parser = argparse.ArgumentParser(description="ARIA model lifecycle CLI")
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("dataset-build")
    build.add_argument("--source", required=True)
    build.add_argument("--output", required=True)
    build.add_argument("--name", default="aria-sft")
    build.add_argument("--version", default="v1")

    validate = commands.add_parser("dataset-validate")
    validate.add_argument("--manifest", required=True)

    audit = commands.add_parser("dataset-audit")
    audit.add_argument("--source", required=True)
    audit.add_argument("--benchmark", required=True)
    audit.add_argument("--output", required=True)
    audit.add_argument("--contamination-threshold", type=float, default=0.8)
    audit.add_argument("--minimum-quality", type=float, default=0.9)

    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--predictions", required=True)
    evaluate.add_argument("--model", required=True)
    evaluate.add_argument("--output", required=True)
    evaluate.add_argument("--benchmark", default="aria-eval-v1")

    register = commands.add_parser("register")
    register.add_argument("--artifact", required=True)
    register.add_argument("--registry", required=True)
    register.add_argument("--name", required=True)
    register.add_argument("--version", required=True)
    register.add_argument("--base-model", required=True)
    register.add_argument("--dataset-manifest", required=True)
    register.add_argument("--scorecard", required=True)

    promote = commands.add_parser("promotion-check")
    promote.add_argument("--scorecard", required=True)

    compare = commands.add_parser("promotion-compare")
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--candidate", required=True)
    compare.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "dataset-build":
        result = build_dataset(args.source, args.output, name=args.name, version=args.version)
        print(json.dumps({"manifest": str(result.manifest_path), "records": result.manifest.record_count, "duplicates": result.duplicate_count, "redactions": result.redaction_count}, indent=2))
    elif args.command == "dataset-validate":
        print(json.dumps(asdict(validate_built_dataset(args.manifest)), indent=2, sort_keys=True))
    elif args.command == "dataset-audit":
        report = audit_dataset(args.source, args.benchmark, threshold=args.contamination_threshold)
        report.write(args.output)
        enforce_audit(report, minimum_quality=args.minimum_quality)
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    elif args.command == "evaluate":
        scorecard = evaluate_file(args.predictions, args.model, args.benchmark)
        scorecard.write(args.output)
        print(json.dumps(asdict(scorecard), indent=2, sort_keys=True))
    elif args.command == "register":
        print(register_model(args.artifact, args.registry, name=args.name, version=args.version, base_model=args.base_model, dataset_manifest=args.dataset_manifest, scorecard=args.scorecard))
    elif args.command == "promotion-check":
        payload = json.loads(open(args.scorecard, encoding="utf-8").read())
        decision = evaluate_promotion(payload)
        print(json.dumps(asdict(decision), indent=2, sort_keys=True))
        raise SystemExit(0 if decision.approved else 2)
    elif args.command == "promotion-compare":
        baseline = json.loads(open(args.baseline, encoding="utf-8").read())
        candidate = json.loads(open(args.candidate, encoding="utf-8").read())
        decision = compare_for_promotion(baseline, candidate)
        payload = {**asdict(decision), "baseline": baseline["model"], "candidate": candidate["model"]}
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit(0 if decision.approved else 2)


if __name__ == "__main__":
    main()
