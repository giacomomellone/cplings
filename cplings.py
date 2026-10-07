#!/usr/bin/env python3
"""Build, test, and watch one exercise at a time using the existing CMake targets."""

import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
PROGRESS = ROOT / ".cplings-progress.txt"


def load_progress(names):
    completed = set(PROGRESS.read_text().splitlines()) if PROGRESS.exists() else set()
    unknown = completed.difference(names)
    if unknown:
        raise ValueError(f"Unknown exercises in {PROGRESS.name}: {', '.join(sorted(unknown))}")
    return completed


def save_progress(completed, names):
    temporary = PROGRESS.with_suffix(".tmp")
    temporary.write_text("".join(f"{name}\n" for name in names if name in completed))
    temporary.replace(PROGRESS)


def cmake_list(path, name):
    # ponytail: reads the current literal CMake lists; generate a manifest if they become dynamic.
    contents = re.sub(r"#[^\n]*", "", path.read_text())
    return re.search(rf"set\({name}\s+([^)]*)\)", contents).group(1).split()


def exercises():
    return [
        ROOT / "exercises" / chapter / f"{name}.cpp"
        for chapter in cmake_list(ROOT / "CMakeLists.txt", "CHAPTERS")
        for name in cmake_list(ROOT / "exercises" / chapter / "CMakeLists.txt", "EXERCISES")
    ]


def snapshot():
    paths = [ROOT / "CMakeLists.txt"]
    for folder in ("exercises", "include", "tests"):
        paths.extend(path for path in (ROOT / folder).rglob("*") if path.is_file())
    # ponytail: poll this small repo; use a filesystem watcher if its size makes polling costly.
    return {path: (path.stat().st_mtime_ns, path.stat().st_size) for path in paths}


def check(source, build):
    if subprocess.run(
        ["cmake", "--build", str(build), "--target", source.stem, "--config", "Debug"],
        cwd=ROOT,
    ).returncode:
        return False
    executable = build / source.parent.relative_to(ROOT) / source.stem
    if os.name == "nt":
        executable = executable.with_suffix(".exe")
    if not executable.exists():
        executable = executable.parent / "Debug" / executable.name
    # POST_BUILD doesn't run when a target is up to date, so always run its tests.
    return subprocess.run([str(executable)], cwd=ROOT).returncode == 0


@contextmanager
def keyboard():
    if os.name == "posix" and sys.stdin.isatty():
        import termios
        import tty

        original = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            yield
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original)
    else:
        yield


def read_key():
    if os.name == "nt":
        import msvcrt

        time.sleep(0.1)
        return msvcrt.getwch().lower() if msvcrt.kbhit() else ""
    if select.select([sys.stdin], [], [], 0.1)[0]:
        key = os.read(sys.stdin.fileno(), 1).decode().lower()
        return key or "q"
    return ""


def wait(passed, automatic, before):
    print("Passed!" if passed else "Failed. Save your changes to retry.", flush=True)
    print("[n] next after passing  [r] retry  [q] quit", flush=True)
    deadline = time.monotonic() + 3 if passed and automatic else None
    if deadline is not None:
        print("Next exercise in 3 seconds…", flush=True)
    with keyboard():
        while True:
            if snapshot() != before:
                return "r"
            key = read_key()
            if key in ("q", "r"):
                return key
            if passed and (key == "n" or (deadline is not None and time.monotonic() >= deadline)):
                return "n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--auto", action="store_true", help="advance 3 seconds after tests pass")
    parser.add_argument("--start", metavar="EXERCISE", help="start at an exercise, e.g. variables2")
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build")
    args = parser.parse_args()
    ordered = exercises()
    names = [source.stem for source in ordered]
    if args.start and args.start not in names:
        parser.error(f"unknown exercise: {args.start}")
    try:
        completed = load_progress(names)
    except ValueError as error:
        parser.error(str(error))
    index = names.index(args.start) if args.start else next(
        (i for i, name in enumerate(names) if name not in completed), len(names)
    )
    if index == len(names):
        print("All exercises completed! Use --start EXERCISE to revisit one.")
        return 0
    build = args.build_dir.resolve()
    if subprocess.run(["cmake", "-S", str(ROOT), "-B", str(build)], cwd=ROOT).returncode:
        return 1
    starting = True
    while index < len(ordered):
        source = ordered[index]
        if not args.start and source.stem in completed:
            index += 1
            continue
        print(f"\n[{index + 1}/{len(ordered)}] {source.relative_to(ROOT)}", flush=True)
        before = snapshot()
        passed = check(source, build)
        if passed:
            completed.add(source.stem)
        else:
            completed.discard(source.stem)
        save_progress(completed, names)
        if starting and passed:
            print("Already passing; moving on.", flush=True)
            index += 1
            continue
        starting = False
        action = wait(passed, args.auto, before)
        if action == "q":
            return 0
        if action == "n":
            index += 1
    print("All exercises passed!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(130)
    except OSError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
