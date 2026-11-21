#!/usr/bin/env python3
"""Open a finished or in-progress Shotkit run in an installed Canvas workspace."""
import argparse
import os
from pathlib import Path


def run_root(value):
    path = value.expanduser().absolute()
    nested = path / "output"
    output = nested if (nested / "run.json").exists() else path
    if (output / "run.json").is_file() and (output / "shots.json").is_file():
        return (output.parent if output.name == "output" else output).resolve()
    raise ValueError(f"{path} has no Shotkit run. Choose a folder with run.json and shots.json, or its project folder.")


def runtime_launcher(value):
    if not value:
        raise ValueError("Point --runtime or SHOTKIT_CANVAS_HOME at your local Shotkit Canvas installation.")
    root = Path(value).expanduser().resolve()
    launcher = root / "start.sh"
    if not launcher.is_file() or not os.access(launcher, os.X_OK) or not (root / "serve.py").is_file():
        raise ValueError(f"{root} has no usable Canvas launcher. Check --runtime or SHOTKIT_CANVAS_HOME.")
    api = root / "WORKSPACE_API"
    if not api.is_file() or api.read_bytes().strip() != b"1":
        raise ValueError(f"{root} is incompatible. Use the Canvas archive with workspace API 1.")
    return launcher


def main():
    parser = argparse.ArgumentParser(
        prog="sk workspace", description="Open a run in a separately installed Shotkit Canvas workspace.",
    )
    parser.add_argument("run", metavar="RUN_OR_OUTPUT_DIR", type=Path, nargs="?")
    parser.add_argument("--runtime", type=Path, help="Canvas installation folder (defaults to SHOTKIT_CANVAS_HOME)")
    parser.add_argument("--port", type=int, help="local port (0 chooses an available port)")
    parser.add_argument("--rules-only", action="store_true", help="use local rules instead of Claude")
    parser.add_argument("--isolated", action="store_true", help="skip discovery of other projects and saved keys")
    parser.add_argument("--open", action="store_true", help="open the selected run in your browser")
    parser.add_argument("--doctor", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    runtime = args.runtime or os.environ.get("SHOTKIT_CANVAS_HOME")
    if args.doctor:
        try:
            print(f"  canvas   {runtime_launcher(runtime).parent}")
        except (OSError, RuntimeError, ValueError) as error:
            print(f"  canvas   optional. {error}")
        return

    if args.run is None:
        parser.error("RUN_OR_OUTPUT_DIR is required.")
    if args.port is not None and not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535.")
    try:
        project = run_root(args.run)
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    try:
        launcher = runtime_launcher(runtime)
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(f"{error} For the portable board, use sk board RUN_OR_OUTPUT_DIR --open.")

    command = [str(launcher), str(project)]
    if args.port is not None:
        command.extend(("--port", str(args.port)))
    if args.rules_only:
        command.append("--rules-only")
    if args.isolated:
        command.append("--isolated")
    if args.open:
        command.append("--open")
    try:
        os.chdir(launcher.parent)
        os.execv(launcher, command)
    except OSError as error:
        parser.exit(1, f"sk workspace: could not start Canvas: {error}\n")


if __name__ == "__main__":
    main()
