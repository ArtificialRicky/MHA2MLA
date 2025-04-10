import argparse
import os
from dataclasses import asdict
from pprint import pformat

from lighteval.parsers import parser_accelerate, parser_baseline, parser_nanotron, parser_utils_tasks
from lighteval.tasks.registry import Registry, taskinfo_selector
import yaml


CACHE_DIR = os.getenv("HF_HOME")


# copied from lighteval.main
def cli_evaluate():  # noqa: C901
    parser = argparse.ArgumentParser(description="CLI tool for lighteval, a lightweight framework for LLM evaluation")
    parser.add_argument(
        "--cfg_RoPE",
        type=str,
        required=True,
        help="Path to the RoPE configuration file. This file should contain the RoPE configuration.",
    )

    subparsers = parser.add_subparsers(help="help for subcommand", dest="subcommand")

    # Subparser for the "accelerate" command
    parser_a = subparsers.add_parser("accelerate", help="use accelerate and transformers as backend for evaluation.")
    parser_accelerate(parser_a)

    # Subparser for the "nanotron" command
    parser_b = subparsers.add_parser("nanotron", help="use nanotron as backend for evaluation.")
    parser_nanotron(parser_b)

    parser_c = subparsers.add_parser("baseline", help="compute baseline for a task")
    parser_baseline(parser_c)

    # Subparser for task utils functions
    parser_d = subparsers.add_parser("tasks", help="display information about available tasks and samples.")
    parser_utils_tasks(parser_d)

    args = parser.parse_args()

    # Monkey patching for the partial rope
    from .patch_func_hf import ae_patch_func_hf
    with open(args.cfg_RoPE,"r") as f:
        cfg_RoPE = yaml.load(f, Loader=yaml.FullLoader)
        cfg_RoPE=cfg_RoPE["model"]["model_config"]["RoPE"]
    ae_patch_func_hf(cfg_RoPE)

    if args.subcommand == "accelerate":
        from lighteval.main_accelerate import main as main_accelerate

        main_accelerate(args)

    elif args.subcommand == "nanotron":
        from lighteval.main_nanotron import main as main_nanotron

        main_nanotron(args.checkpoint_config_path, args.lighteval_config_path, args.cache_dir)

    elif args.subcommand == "baseline":
        from lighteval.main_baseline import main as main_baseline

        main_baseline(args)

    elif args.subcommand == "tasks":
        registry = Registry(cache_dir=args.cache_dir, custom_tasks=args.custom_tasks)
        if args.list:
            registry.print_all_tasks()

        if args.inspect:
            print(f"Loading the tasks dataset to cache folder: {args.cache_dir}")
            print(
                "All examples will be displayed without few shot, as few shot sample construction requires loading a model and using its tokenizer. "
            )
            # Loading task
            task_names_list, _ = taskinfo_selector(args.inspect, task_registry=registry)
            task_dict = registry.get_task_dict(task_names_list)
            for name, task in task_dict.items():
                print("-" * 10, name, "-" * 10)
                if args.show_config:
                    print("-" * 10, "CONFIG")
                    task.cfg.print()
                for ix, sample in enumerate(task.eval_docs()[: int(args.num_samples)]):
                    if ix == 0:
                        print("-" * 10, "SAMPLES")
                    print(f"-- sample {ix} --")
                    print(pformat(asdict(sample), indent=1))
    else:
        print("You did not provide any argument. Exiting")


if __name__ == "__main__":
    cli_evaluate()
