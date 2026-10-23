import argparse
import os
import sys
from typing import Optional

from .generate import run_generation, normalize_model_slug
from .run_official_eval import run_official_evaluation
from .analyze_failures import run_failure_analysis


def run_full_pipeline(
    model: str = "qwen2.5-coder:7b",
    setup: str = "schema",
    num: Optional[int] = None,
    output_dir: str = os.path.join("execution_eval_suite", "results"),
    skip_generate: bool = False,
    skip_official: bool = False,
    timeout: int = 180
):
    print("=" * 80)
    print(f"  TEXT-TO-SQL EXPERIMENT PIPELINE")
    print(f"  Model: {model} | Setup: {setup} | Questions: {num if num else 'ALL (500)'}")
    print("=" * 80 + "\n")

    model_slug = normalize_model_slug(model)
    os.makedirs(output_dir, exist_ok=True)
    predict_file = os.path.join(output_dir, f"predict_{setup}_{model_slug}.json")
    details_file = os.path.join(output_dir, f"details_{setup}_{model_slug}.json")

    # Step 1: SQL Generation
    if not skip_generate:
        print("\n>>> STEP 1: SQL GENERATION (Ollama API + Latency Tracking)")
        run_generation(
            model=model,
            setup=setup,
            num=num,
            output_dir=output_dir,
            timeout=timeout
        )
    else:
        print(f"\n>>> STEP 1: Skipped generation (using existing {predict_file})")

    if not os.path.exists(predict_file):
        raise FileNotFoundError(f"Prediction file not found: {predict_file}")

    # Step 2: Official Benchmark Evaluation
    if not skip_official:
        print("\n>>> STEP 2: OFFICIAL BIRD BENCHMARK EVALUATOR")
        try:
            eval_res = run_official_evaluation(
                predicted_sql_path=predict_file,
                output_log_path=os.path.join(output_dir, f"eval_{setup}_{model_slug}.txt"),
                num_cpus=4
            )
            print(f"Official EX Score: {eval_res.get('total_acc')}%")
        except Exception as e:
            print(f"Warning: Official evaluator failed or was interrupted: {e}")
    else:
        print("\n>>> STEP 2: Skipped official evaluation.")

    # Step 3: Execution Failure & Metrics Diagnostics
    print("\n>>> STEP 3: EXECUTION FAILURE & DETAILED ERROR DIAGNOSTICS")
    analysis_res = run_failure_analysis(
        predicted_path=predict_file,
        details_path=details_file if os.path.exists(details_file) else None,
        output_dir=output_dir
    )

    print("\n" + "=" * 80)
    print(f"  ALL PIPELINE STEPS COMPLETE FOR {model} ({setup})")
    print(f"  - Predictions : {predict_file}")
    print(f"  - Report      : {os.path.join(output_dir, f'analysis_predict_{setup}_{model_slug}.md')}")
    print(f"  - Metrics JSON: {os.path.join(output_dir, f'analysis_predict_{setup}_{model_slug}.json')}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="End-to-end BIRD benchmark evaluation pipeline.")
    parser.add_argument("--model", type=str, default="qwen2.5-coder:7b", help="Model name in Ollama")
    parser.add_argument("--setup", type=str, choices=["schema", "pruned_v2"], default="schema", help="Prompt setup")
    parser.add_argument("--num", type=int, default=None, help="Number of questions (default 500)")
    parser.add_argument("--output_dir", type=str, default=os.path.join("execution_eval_suite", "results"))
    parser.add_argument("--skip_generate", action="store_true", help="Skip generation if predict JSON exists")
    parser.add_argument("--skip_official", action="store_true", help="Skip official evaluation script")
    parser.add_argument("--timeout", type=int, default=180, help="Generation timeout in seconds")
    args = parser.parse_args()

    run_full_pipeline(
        model=args.model,
        setup=args.setup,
        num=args.num,
        output_dir=args.output_dir,
        skip_generate=args.skip_generate,
        skip_official=args.skip_official,
        timeout=args.timeout
    )


if __name__ == "__main__":
    main()
