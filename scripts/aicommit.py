#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import urllib.request

from dotenv import load_dotenv

load_dotenv()

class colors:
    GRAY = "\033[90m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    RESET = "\033[0m"


def log(message="", color=colors.RESET, end="\n"):
    sys.stdout.write(f"{color}{message}{colors.RESET}{end}")
    sys.stdout.flush()


def errlog(message="", color=colors.RED, end="\n"):
    sys.stderr.write(f"{color}{message}{colors.RESET}{end}")
    sys.stderr.flush()


def info(message="", color=colors.BLUE, end="\n"):
    log(f"✔️ {message}", color, end)


def process(message="", color=colors.CYAN, end="\n"):
    log(f"⏩ {message}", color, end)


def prompt(message="", color=colors.YELLOW, end="\n"):
    log(f"❓ {message}", color, end)


def success(message="", color=colors.GREEN, end="\n"):
    log(f"✅ {message}", color, end)


def warn(message="", color=colors.YELLOW, end="\n"):
    errlog(f"⚠️ {message}", color, end)


def fail(message="", color=colors.RED, end="\n"):
    errlog(f"✖ {message}", color, end)


INIT_MAIN_PROMPT = (
    "Generate a concise and informative Git commit message based on the following changes.\n"
    "Follow the Conventional Commits format:\n"
    "<type>(<scope>): <description>\n"
    "\n"
    "<body>\n"
    "\n"
    "[Optional Footer]\n"
    "\n"
    "Types: feat, fix, docs, style, refactor, test, chore, perf, ci, revert.\n"
    "The description should be in imperative mood and no longer than 74 characters.\n"
    "The body should explain the what and why of the change, wrapped at 72 characters.\n"
    "The footer can include 'BREAKING CHANGE' or reference issues (e.g., 'Closes #123')."
)

def create_payload_json(model):
    return {
        "contents": [
            {"role": "user", "parts": [{"text": INIT_MAIN_PROMPT}]},
        ],
        "generation_config": {
            "temperature": 0.2,
            "topP": 0.8,
            "topK": 10,
            "maxOutputTokens": 1024,
        }
    }

def generate_commit_message(api_url, header, payload_json):
    return llm_api_call(
        api_url,
        method="POST",
        data=payload_json,
        header=header
    )


def llm_api_call(url, method="GET", data=None, header=None):
    request = urllib.request.Request(url, method=method)

    if data:
        request.data = json.dumps(data).encode("utf-8")
    if header:
        for key, value in header.items():
            request.add_header(key, value)
    try:
        with urllib.request.urlopen(request) as response:
            if response.status >= 400:
                raise ValueError(f"Error occurred: {response.status} {response.reason}")
            return handle_urlopen_response(response)

    except Exception as e:
        fail(f"Error occurred: {e}")
        return None


def handle_urlopen_response(response):
    response_content = response.read().decode("utf-8")
    if args.debug:  # Print raw response in debug mode
        print("Raw response:")
        print(response_content)
    return parse_response(response_content)


def parse_response(chunk: str):
    response = json.loads(chunk)
    message = response["candidates"][0]['content']
    log(message["parts"][0]["text"], color=colors.GREEN, end="")
    return message


def create_message(message, role="user"):
    return {"role": role, "parts": [{"text": message}]}


def run_command(command):
    try:
        output = subprocess.check_output(command, text=True)
        return output.strip()
    except subprocess.CalledProcessError as e:
        fail(f"Error running command: {e}")
        raise e


def exclude_from_diff(path):
    info(f"Excluding `{path}` from diff", color=colors.CYAN)
    return f":(exclude){path}"


def get_files_to_exclude():
    command = ["git", "rev-parse", "--show-toplevel"]
    repo_path = run_command(command)
    ignore_file = os.path.join(repo_path, ".aicommitignore")

    files_to_exclude = []
    if os.path.exists(ignore_file):
        with open(ignore_file, encoding="utf-8") as f:
            lines = f.readlines()
        files_to_exclude.extend([exclude_from_diff(line.strip()) for line in lines])
    return files_to_exclude


def get_staged_diff(exclude_files=None):
    exclude_files_args = []
    files_to_exclude = get_files_to_exclude()
    if exclude_files:
        exclude_files_args.extend([exclude_from_diff(f) for f in exclude_files])

    diff_cached = ["diff", "--cached", "--diff-algorithm=minimal"]

    file_command = ["git"] + diff_cached + ["--name-only"] + files_to_exclude + exclude_files_args

    files = run_command(file_command)

    if not files:
        return
    diff_command = ["git"] + diff_cached + files_to_exclude + exclude_files_args
    diff = run_command(diff_command)

    return {"files": files.split("\n"), "diff": diff}


def git_commit(commit_message):
    command = ["git", "commit", "-m", commit_message]
    response = subprocess.run(command, capture_output=True, check=False)
    log(response.stdout.decode("utf-8"), color=colors.GREEN)
    log(response.stderr.decode("utf-8"), color=colors.YELLOW)
    return response.returncode == 0


def prompt_commit():
    while True:
        prompt(
            "Do you want to commit the changes? (y/n): ",
            color=colors.YELLOW,
            end="",
        )
        choice = input()
        if choice.lower() in ["y", "n"]:
            return choice.lower() == "y"
        fail(f"Please enter 'y' or 'n'. Invalid Choice: {choice}")


def generate_and_commit(api_url, header, payload_json):
    log("⚡ Generating commit message...", color=colors.BLUE)
    while True:
        log("—" * 50, color=colors.GRAY)
        response_message = generate_commit_message(api_url, header, payload_json)
        if not response_message:
            fail("Failed to generate commit message.")
            sys.exit(1)

        # Remove the previous model response if it exists
        if payload_json["contents"][-1]["role"] == "model":
            payload_json["contents"].pop()

        # Append the response to contents
        payload_json["contents"].append(response_message)
        log()
        log("—" * 50, color=colors.GRAY)
        log("📝 Commit message generated")

        # Access content correctly from response_message
        commit_message = response_message["parts"][0]["text"]

        if prompt_commit():
            log("Committing changes...", color=colors.BLUE)
            if git_commit(commit_message):
                success("Changes committed successfully!")
                break
            fail("Failed to commit changes.")
            sys.exit(1)
        prompt(
            "Do you want to generate another commit message? (y/n): ",
            color=colors.YELLOW,
            end="",
        )
        choice = input()
        if choice.lower() == "y":
            followup_message = get_followup_message()
            payload_json["contents"].append(
                {"role": "user", "parts": [{"text": followup_message}]}
            )
            log("⚡ Generating new commit message...", color=colors.MAGENTA)
            continue
        break


def get_followup_message():
    prompt("Any feedback to add? (y/n): ", color=colors.YELLOW, end="")
    feedback_choice = input()
    followup_message = "I would like to generate a new commit, but the previous commit is not good."
    if feedback_choice.lower() == "y":
        log("⏩ Enter feedback: ", color=colors.BLUE, end="")
        followup_message = input()
    return followup_message


def main(base_url, api_key, model, exclude_files=None, debug=False):
    diff_files = get_staged_diff(exclude_files)
    if not diff_files:
        info("No staged changes found. Exiting...")
        return

    payload_json = create_payload_json(model)
    payload_json["contents"][-1]["parts"].append({"text": diff_files["diff"]})
    api_url = f"{base_url}/models/{model}:generateContent?key={api_key}"
    header = {"Content-Type": "application/json"}
    generate_and_commit(api_url, header, payload_json)

    if debug:
        for content in payload_json["contents"]:
            info(f"{content['role']}".title(), color=colors.MAGENTA)
            for part in content["parts"]:
                log(f"{part['text']}", color=colors.GRAY)
            log("-" * 50, color=colors.GRAY)

    success("Thank you for using the AI Commit Generator!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate concise git commit messages using LLM.")

    parser.add_argument(
        "-u",
        "--base_url",
        type=str,
        default=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
        help="Base URL of the Gemini API.",
    )
    parser.add_argument(
        "-k",
        "--api_key",
        type=str,
        default=os.getenv("GEMINI_API_KEY"),
        help="API key of the Gemini API.",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=os.getenv("GEMINI_MODEL_NAME", "gemini-pro"),
        help="Name of the Gemini model to use.",
    )
    parser.add_argument(
        "-e",
        "--exclude_files",
        nargs="*",
        default=[],
        help="List of files to exclude from the diff",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    args = parser.parse_args()

    try:
        main(
            args.base_url,
            args.api_key,
            args.model,
            args.exclude_files,
            args.debug
        )
    except KeyboardInterrupt:
        fail("Interrupted by user.")
        sys.exit(1)