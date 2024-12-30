#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import urllib.request

from dotenv import load_dotenv

load_dotenv()

# ... (colors class and logging functions remain the same) ...

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
    # sys.stdout.write(color + message + colors.RESET + end)
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
   

    "You are to act as the author of a commit message in git. "
    "Your mission is to create clean and comprehensive commit "
    "messages as per the conventional commit convention and "
    "explain WHAT were the changes and mainly WHY the changes "
    "were done. I'll send you an output of 'git diff --staged' "
    "command, and you are to convert it into a commit message.\n"
    "Do not preface the commit with anything. User can take "
    "followup with you and share the feedback if user have some "
    "concern with generated commit message.\n"
    "Conventional commit keywords:\n"
    "    fix: A bug fix. Correlates with PATCH in SemVer\n"
    "    feat: A new feature. Correlates with MINOR in SemVer\n"
    "    docs: Documentation only changes\n"
    "    style: Changes that do not affect the meaning of the code "
    "(white-space, formatting, missing semi-colons, etc)\n"
    "    refactor: A code change that neither fixes a bug nor adds a feature\n"
    "    perf: A code change that improves performance\n"
    "    test: Adding missing or correcting existing tests\n"
    "    build: Changes that affect the build system or external "
    "dependencies (example scopes: pip, docker, npm)\n"
    "    ci: Changes to our CI configuration files and scripts (example"
    "scopes: GitLabCI)\n"
    "    chore: Other changes that don't modify src or test files\n"
    "    BREAKING CHANGE(optional): a commit that has the text BREAKING CHANGE:"
    " at the beginning of its optional body or footer section introduces a "
    "breaking API change (correlating with MAJOR in semantic versioning)."
    "Add a short description of WHY the changes are done after the "
    'commit message. Don\'t start it with "This commit", just '
    "describe the changes.\n"
    "Description of commit is composed of body. it should start with "
    "summary and then in bullet points which highlight the key points.\n"
    "\n"
    "Craft a concise commit message that encapsulates all changes "
    "made, with an emphasis on the primary updates. If the "
    "modifications share a common theme or scope, mention it "
    "succinctly; otherwise, leave the scope out to maintain focus. "
    "The goal is to provide a clear and unified overview of the "
    "changes in a one single message, without diverging into a "
    "list of commit per file change."
    "Use the present tense. Lines must not be longer than 74 characters. "
    "Use english for the commit message.\n"
    "\n"
    "You will strictly follow the following conventions to generate "
    "the content of the commit message\n"
    "A scope may be provided to a commit's type, to provide additional "
    "contextual information and is contained within parenthesis.\n"
    "\n<type>(<scope>): <description>"
    "\n<BLANK LINE>"
    "\n<body>"
    "\n<BLANK LINE>"
    "\n[(BREAKING CHANGE: ) <footer>]"

)

# ... (generate_system_message function remains the same) ...

# Function to generate the system message template
def generate_system_message():
    return (
        "You are to act as the author of a commit message in git. "
        "Your mission is to create clean and comprehensive commit "
        "messages as per the conventional commit convention and "
        "explain WHAT were the changes and mainly WHY the changes "
        "were done. which generate concise git commit messages in "
        "present tense from output of 'git diff --staged' command "
        "with the given specifications below:"
        "\nMessage language: en"
        "\nExclude anything unnecessary such as translation. Your entire "
        "response will be passed directly into git commit."
        "\nThe commit contains the following structural elements, to "
        "communicate intent to the consumers of your library:"
        "\n    fix: A bug fix. Correlates with PATCH in SemVer"
        "\n    feat: A new feature. Correlates with MINOR in SemVer"
        "\n    docs: Documentation only changes"
        "\n    style: Changes that do not affect the meaning of the code "
        "(white-space, formatting, missing semi-colons, etc)"
        "\n    refactor: A code change that neither fixes a bug nor adds a "
        "feature"
        "\n    perf: A code change that improves performance"
        "\n    test: Adding missing or correcting existing tests"
        "\n    build: Changes that affect the build system or external "
        "dependencies (example scopes: pip, docker, npm)"
        "\n    ci: Changes to our CI configuration files and scripts (example "
        "scopes: GitLabCI)"
        "\n    chore: Other changes that don't modify src or test files"
        "\n    BREAKING CHANGE: a commit that has the text BREAKING CHANGE: at "
        "the beginning of its optional body or footer section introduces a "
        "breaking API change (correlating with MAJOR in semantic versioning)."
        "\nChoose a type that best describes the git diff."
        "\nNotice these types are not mandated by the conventional commits "
        "specification, and have no implicit effect in semantic versioning "
        "(unless they include a BREAKING CHANGE)."
        "\nA scope may be provided to a commit's type, to provide additional "
        "contextual"
        "\ninformation and is contained within parenthesis, e.g., feat(parser):"
        " add ability to parse arrays."
        "\n"
        "\n<type>(<scope>): <description>"
        "\n<BLANK LINE>"
        "\n<body>"
        "\n<BLANK LINE>"
        "\n[optional (BREAKING CHANGE: ) <footer>]"
    )



def create_payload_json(
    model,
    stream=True,
):
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": INIT_MAIN_PROMPT},
        ],
        "stream": stream,
    }

# ... (generate_commit_message, llm_api_call, handle_urlopen_response, 
#      parse_response, parse_response_chunk, get_message, get_content, 
#      create_message, run_command, exclude_from_diff, get_files_to_exclude, 
#      get_staged_diff, git_commit, prompt_commit, generate_and_commit, 
#      get_followup_message functions remain the same) ...


def generate_commit_message(api_url, header, payload_json, stream):
    return llm_api_call(
        api_url,
        method="POST",
        data=payload_json,
        header=header,
        stream=stream,
    )


def llm_api_call(url, method="GET", data=None, header=None, stream=False):
    # Create a request object
    request = urllib.request.Request(url, method=method)

    # If data is provided, encode it and add it to the request
    if data:
        request.data = json.dumps(data).encode("utf-8")
    if header:
        for key, value in header.items():
            request.add_header(key, value)
    try:
        # Open the URL with the request
        with urllib.request.urlopen(request) as response:
            if response.status >= 400:
                raise ValueError(f"Error occurred: {response.status} {response.reason}")
            return handle_urlopen_response(response, stream)

    except Exception as e:
        fail(f"Error occurred: {e}")
        return None


def handle_urlopen_response(response, stream=False):
    if not stream:
        return parse_response(response.read().decode("utf-8"))
    message = ""
    for line in response:
        # Process each line of the streaming response
        content = parse_response_chunk(line.decode("utf-8").strip())
        message += content

    return create_message(message, role="assistant")


def parse_response(chunk: str):
    response = json.loads(chunk)
    message = get_message(response)
    content = get_content(message)
    log(content, color=colors.GREEN, end="")
    return message


def parse_response_chunk(chunk: str):
    if not (chunk and chunk.startswith("data: ")):
        return ""
    chunk = chunk[6:]
    if chunk == "[DONE]":
        return ""
    chunk_json = json.loads(chunk)
    if chunk_json["choices"][0]["finish_reason"] == "stop":
        return ""
    content = chunk_json["choices"][0]["delta"]["content"]
    log(content, color=colors.GREEN, end="")
    return content


def get_message(data):
    return data["choices"][0]["message"]


def get_content(message):
    return message["content"]


def create_message(message, role="user"):
    return {"role": role, "content": message}


# Function to run shell commands
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
    # Decode stdout and stderr
    log(response.stdout.decode("utf-8"), color=colors.GREEN)
    log(response.stderr.decode("utf-8"), color=colors.YELLOW)
    return response.returncode == 0


# Function to prompt user for commit confirmation
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


def generate_and_commit(api_url, header, payload_json, stream):
    log("⚡ Generating commit message...", color=colors.BLUE)
    while True:
        log("—" * 50, color=colors.GRAY)
        response_message = generate_commit_message(api_url, header, payload_json, stream)
        if not response_message:
            fail("Failed to generate commit message.")
            sys.exit(1)
        payload_json["messages"].append(response_message)
        log()
        log("—" * 50, color=colors.GRAY)
        log("📝 Commit message generated")
        commit_message = get_content(response_message)

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
            payload_json["messages"].append(create_message(followup_message, role="user"))
            log("⚡ Generating new commit message...", color=colors.MAGENTA)
            continue
        break


def get_followup_message():
    prompt("Any feedback to add? (y/n): ", color=colors.YELLOW, end="")
    feedback_choice = input()
    followup_message = "I would like to generate a new commit, " "but the previous commit is not good."
    if feedback_choice.lower() == "y":
        log("⏩ Enter feedback: ", color=colors.BLUE, end="")
        followup_message = input()
    return followup_message



def main(base_url, api_key, model, stream=True, exclude_files=None, debug=False):
    diff_files = get_staged_diff(exclude_files)
    if not diff_files:
        info("No staged changes found. Exiting...")
        return
    api_url = f"{base_url}/chat/completions"  # This might need to be adjusted for Gemini
    
    diff_files = get_staged_diff(exclude_files)
    
    payload_json = create_payload_json(model, stream=stream)
    payload_json["messages"].append(create_message(diff_files["diff"], role="user"))
    api_url = f"{base_url}/models/{model}:generateContent?key={api_key}"
    print (api_url)
    header = {"Content-Type": "application/json"}
    generate_and_commit(api_url, header, payload_json, stream)
    if debug:
        for message in payload_json["messages"]:
            info(f"{message['role']}".title(), color=colors.MAGENTA)
            log(f"{message['content']}", color=colors.GRAY)
            log("-" * 50, color=colors.GRAY)

    success("Thank you for using the AI Commit Generator!")
    


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate concise git commit messages using LLM.")
    
    # ... (Other arguments remain the same) ...

    parser.add_argument(
        "-u",
        "--base_url",
        type=str,
        default=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),  # Update base URL -"https://api.google.com/v1/generativeai"
        help="Base URL of the Gemini API.",
    )
    parser.add_argument(
        "-k",
        "--api_key",
        type=str,
        default=os.getenv("GEMINI_API_KEY"),  # Use GEMINI_API_KEY
        help="API key of the Gemini API.",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=os.getenv("GEMINI_MODEL_NAME", "gemini-pro"),  # Update model name
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
    
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming of the commit message generation",
    )

    # ... (The rest of the argument parsing remains the same) ...

    args = parser.parse_args()

    try:
       main(
            args.base_url,
            args.api_key,
            args.model,
            not args.no_stream,  # Use no-stream flag to control streaming
            args.exclude_files,
            args.debug
        )
    except KeyboardInterrupt:
        fail("Interrupted by user.")
        sys.exit(1)