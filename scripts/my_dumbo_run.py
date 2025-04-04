#!/usr/bin/env .venv/bin/python
import getpass
import os
import subprocess


def run_qrcode_openrouter_evaluation():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = getpass.getpass("Enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = api_key
    cmd = [
        ".venv/bin/python",
        "-m",
        "lm_eval",
        "--model",
        "openrouter-chat",
        "--model_args",
        "base_url=https://openrouter.ai/api/v1/chat/completions,model=google/gemma-3-27b-it,chat_formatting_function=None",
        "--tasks",
        "qrcode",
        "--num_fewshot",
        "0",
        "--limit",
        "2",
        "--apply_chat_template",
    ]
    subprocess.run(cmd)


def run_qrcode_with_wandb():
    ### Initial and improved CLI preconception:
    # """ current/latest command """
    # .venv/bin/python -m lm_eval --model openai-chat-completions --model_args "base_url=https://openrouter.ai/api/v1/chat/completions,model=google/gemma-3-27b-it,chat_formatting_function=None" --tasks qrcode --num_fewshot 0 --limit 2 --apply_chat_template --output_path ./qrcode_output.json --log_level DEBUG
    # export OPENAI_API_KEY='sk-or-v1-...' && .venv/bin/python -m lm_eval --model openai-chat-completions --model_args "base_url=https://openrouter.ai/api/v1/chat/completions,model=google/gemma-3-27b-it,chat_formatting_function=None" --tasks qrcode --num_fewshot 0 --limit 2 --apply_chat_template     --wandb_args project=qr-eval  --output_path ./output  --log_samples
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = getpass.getpass("Enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = api_key
    cmd = [
        ".venv/bin/python",
        "-m",
        "lm_eval",
        "--model",
        "openai-chat-completions",
        "--model_args",
        "base_url=https://openrouter.ai/api/v1/chat/completions,model=google/gemma-3-27b-it,chat_formatting_function=None",
        "--tasks",
        "qrcode",
        "--num_fewshot",
        "0",
        "--limit",
        "2",
        "--apply_chat_template",
        "--wandb_args",
        "project=qr-eval",
        "--output_path",
        "./output",
        "--log_samples",
    ]
    subprocess.run(cmd)


if __name__ == "__main__":
    run_qrcode_with_wandb()
    # run_qrcode_openrouter_evaluation() # was always super-weird like stuck in an infinite loop..?!
