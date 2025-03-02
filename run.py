#!/usr/bin/env python3

import sys
from argparse import ArgumentParser
from pathlib import Path
from subprocess import Popen, DEVNULL
from os import chdir, environ
from os.path import dirname


def nice_try(fn):
    try:
        fn()
    except Exception as e:  # noqa: E722
        print(f"<IGNORE> An error occured: {e}.\n</IGNORE> ")


def run(args: str | list) -> Popen:
    print(f"running: {args}")
    proc = Popen(args.split() if isinstance(args, str) else args, env=environ.copy())
    return proc


def wait(args: str | list) -> int:
    return run(args).wait()


def has_uv():
    try:
        x = Popen(["uv", "version"], stdout=DEVNULL).wait() == 0
        return x
    except:
        return False


def is_docker():
    return Path("/.dockerenv").exists()


ACTIONS = {"run", "server", "frontend"}


def parse_args():
    parser = ArgumentParser(
        prog="Management commands for app",
        description=f"Run as: python3 ./run.py [{' / '.join(ACTIONS)}]",
    )
    parser.add_argument("--action", default="run", required=False)
    return parser.parse_args()


def frontend():
    chdir(FRONTEND_DIR)
    wait("pnpm i")
    wait("pnpm run dev")


def server():
    chdir(BACKEND_DIR)
    wait("uv run python -m src.server")


def run_everything():
    proc = [
        run("python3 run.py --action=server"),
        run("python3 run.py --action=frontend"),
    ]
    try:
        for p in proc:
            p.wait()
    except KeyboardInterrupt:
        import signal

        p.send_signal(signal.SIGINT)
        p.wait()
    print("\nkilled")


def install_uv():
    import os

    print("Please run:\n")
    if os.name == "nt":
        print(
            'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
        )
    else:
        print("curl -LsSf https://astral.sh/uv/install.sh | sh")


if __name__ == "__main__":
    chdir(dirname(__file__))
    if not has_uv():
        print(
            "You do not have uv installed!\n"
            "Please install uv.\n"
            "https://github.com/astral-sh/uv"
        )
        install_uv()
        quit()
    BACKEND_DIR = (Path(".") / "backend").resolve()
    FRONTEND_DIR = (Path(".") / "frontend").resolve()
    # print(BACKEND_DIR.resolve())
    sys.path.append(str(BACKEND_DIR.resolve()))
    # print(BACKEND_DIR)
    # print(FRONTEND_DIR)

    args = parse_args()

    match args.action:
        case "server":
            server()
        case "frontend":
            frontend()

        case "run":
            run_everything()
        case arg:
            print(f'Unsupported arg  "{arg}"\navailable: {ACTIONS}')
