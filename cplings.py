#!/usr/bin/env python3
"""Build, test, and watch one exercise at a time using the existing CMake targets."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import select
import shlex
import shutil
import subprocess
import sys
import textwrap
import time

ROOT = Path(__file__).resolve().parent
PROGRESS = ROOT / ".cplings-progress.txt"
SKIPPED = ROOT / ".cplings-skipped.txt"
KEY_BUFFER = ""


def load_progress(names, path=None):
    path = PROGRESS if path is None else path
    completed = set(path.read_text().splitlines()) if path.exists() else set()
    unknown = completed.difference(names)
    if unknown:
        raise ValueError(f"Unknown exercises in {path.name}: {', '.join(sorted(unknown))}")
    return completed


def save_progress(completed, names, path=None):
    path = PROGRESS if path is None else path
    temporary = path.with_suffix(".tmp")
    temporary.write_text("".join(f"{name}\n" for name in names if name in completed))
    temporary.replace(path)


def cmake_list(path, name):
    # ponytail: reads the current literal CMake lists; generate a manifest if they become dynamic.
    contents = re.sub(r"#[^\n]*", "", path.read_text())
    return re.search(rf"set\({name}\s+([^)]*)\)", contents).group(1).split()


def legacy_exercises():
    return [
        ROOT / "exercises" / chapter / f"{name}.cpp"
        for chapter in cmake_list(ROOT / "CMakeLists.txt", "CHAPTERS")
        for name in cmake_list(ROOT / "exercises" / chapter / "CMakeLists.txt", "EXERCISES")
    ]


def lessons():
    return [dict(item, level=level['name'], rank=level['rank'])
            for level in json.loads((ROOT / 'learning_path.json').read_text())['levels']
            for item in level['exercises']]


def exercises(legacy=False):
    return legacy_exercises() if legacy else [ROOT / item['path'] for item in lessons()]


def lesson(source):
    return next((item for item in lessons() if item['name'] == source.stem), None)


def snapshot():
    paths = [ROOT / "CMakeLists.txt", ROOT / "learning_path.json"]
    for folder in ("exercises", "include", "tests"):
        paths.extend(path for path in (ROOT / folder).rglob("*") if path.is_file())
    # ponytail: poll this small repo; use a filesystem watcher if its size makes polling costly.
    return {path: (path.stat().st_mtime_ns, path.stat().st_size) for path in paths}


def check(source, build, report=None):
    if report:
        report("compile", "running", "")
    compiled = subprocess.run(
        ["cmake", "--build", str(build), "--target", source.stem, "--config", "Debug"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    if compiled.returncode:
        if report:
            report("compile", "failed", compiled.stdout)
        return False
    executable = build / source.parent.relative_to(ROOT) / source.stem
    if os.name == "nt":
        executable = executable.with_suffix(".exe")
    if not executable.exists():
        executable = executable.parent / "Debug" / executable.name
    if report:
        report("test", "running", "")
    try:
        tested = subprocess.run(
            [str(executable), "--colour-mode", "none"], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired as error:
        output = error.stdout or b""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        if report:
            report("test", "timeout", output + "\nTest exceeded 30 seconds.")
        return False
    if report:
        status = "passed" if tested.returncode == 0 else "crashed" if tested.returncode < 0 else "failed"
        report("test", status, tested.stdout)
    return tested.returncode == 0


def hint(source):
    path = ROOT / "hints" / source.parent.name / f"{source.stem}.md"
    if path.is_file():
        return path.read_text().strip()
    metadata = lesson(source)
    if metadata:
        return metadata['hint']
    chapter = source.parent / "README.md"
    return "No exercise hint available." + (
        f"\nChapter resources: {chapter.relative_to(ROOT)}" if chapter.is_file() else ""
    )


def learning(source):
    metadata = lesson(source)
    if metadata:
        return f"{metadata['learn']}\n\nBefore editing: {metadata['question']}\n\nAfter passing: explain why the original failed and your change works."
    chapter = source.parent / "README.md"
    return chapter.read_text().strip() if chapter.is_file() else "Read the exercise comments and tests, predict the result, then use h for a hint."


def edit(source):
    try:
        command = shlex.split(os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi")
        result = subprocess.run([*command, str(source)], cwd=ROOT)
        return f"Editor exited with code {result.returncode}." if result.returncode else None
    except (OSError, ValueError) as error:
        return f"Editor: {error}. Set VISUAL or EDITOR to your editor command."


def focused_output(output):
    lines = [line for line in output.splitlines() if not re.match(r"\[\s*\d+%\]|(?:g?make)(?:\[\d+\])?:.*Error \d", line)]
    for index, line in enumerate(lines):
        if re.search(r"(?:fatal )?error:|FAILED:|AddressSanitizer|LeakSanitizer|runtime error:|terminate called", line):
            return "\n".join(lines[max(0, index - 3):index + 9])
    summary = [line for line in lines if re.search(r"All tests passed|test cases:|assertions:|exceeded", line)]
    return "\n".join(summary or lines[-8:])


def colourize(text):
    lines = []
    for line in text.splitlines():
        colour = ""
        if "FAILED" in line or "CRASHED" in line or "TIMEOUT" in line or "error:" in line:
            colour = "31;1"
        elif "PASSED" in line or "All tests passed" in line:
            colour = "32;1"
        elif "RUNNING" in line:
            colour = "34;1"
        elif line in ("HINT", "LEARN"):
            colour = "33;1"
        elif line.startswith(("cplings ", "TEST ", "LEVEL ")):
            colour = "36;1"
        elif line.startswith("exercises/"):
            colour = "36"
        elif line and set(line) == {"-"}:
            colour = "90"
        if colour:
            line = f"\x1b[{colour}m{line}\x1b[0m"
        elif re.match(r"\[(?:[a-z]|j/k|Enter|Tab|l/Esc)\]", line):
            line = re.sub(r"\[(?:[a-z]|j/k|Enter|Tab|l/Esc)\]", lambda match: f"\x1b[36;1m{match[0]}\x1b[0m", line)
        lines.append(line)
    return "\n".join(lines)


def screen(source, index, ordered, completed, view, width=80, height=40):
    width = max(30, min(width, 100))
    ruler = "-" * width
    test_names = re.findall(r'TEST_CASE\s*\(\s*"([^"]+)"', source.read_text())
    test = test_names[0] if test_names else source.stem
    if len(test_names) > 1:
        test += f" (+{len(test_names) - 1} more)"
    catalogue = view.get("catalogue", ordered) if view.get("list") else ordered
    count = sum(item.stem in completed for item in catalogue)
    skipped = view.get("skipped", set())
    skip_count = sum(item.stem in skipped for item in catalogue)
    lines = [f"cplings    {count}/{len(catalogue)} completed    {skip_count} skipped    auto: {'on' if view['automatic'] else 'off'}", ruler, ""]
    if view.get("list"):
        lines.append("LEARNING PATH · Easy > Moderate > Intermediate > Hard > Difficult")
        selected = view.get("selected", index)
        rows = max(1, height - 14)
        offset = max(0, min(selected - rows // 2, len(catalogue) - rows))
        metadata = {item['name']: item for item in lessons()}
        for position in range(offset, min(offset + rows, len(catalogue))):
            item = catalogue[position]
            level = f"L{metadata[item.stem]['rank']}" if item.stem in metadata else "--"
            state = 'done' if item.stem in completed else 'skipped' if item.stem in skipped else 'todo'
            lines.append(f"{'>' if position == selected else ' '} {position + 1:2}  {state:7}  {level}  {item.stem}"[:width])
        chosen = catalogue[selected]
        lines.extend(["", f"Selected: {chosen.stem}", str(chosen.relative_to(ROOT)), "", ruler,
                      "[j/k] select (or arrows)  [Enter] start", "[l/Esc] back  [q] quit"])
    else:
        lines.extend([f"[{index + 1}/{len(ordered)}] {source.stem}", str(source.relative_to(ROOT)), "", f"TEST  {test}"])
        metadata = lesson(source)
        if metadata:
            lines.insert(5, f"LEVEL {metadata['rank']}/5  {metadata['level']} · {metadata['objective']}")
        stage, status = view["stage"], view["status"]
        lines.append(f"[{stage}] {status.upper()}" + ("    [test] NOT RUN" if stage == "compile" else ""))
        if view.get("learn"):
            lines.extend(["", "LEARN", learning(source), "", "t or Esc returns to the test result."])
        elif status == "running":
            lines.extend(["", "Building the current exercise..." if stage == "compile" else "Running its tests..."])
        else:
            output = view.get("output", "")
            output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output).replace(str(ROOT) + os.sep, "")
            lines.extend(["", output if view.get("details") else focused_output(output)])
            if status != "passed":
                lines.extend(["", "Save the file to retry."])
            elif view["automatic"]:
                lines.extend(["", "Auto advance paused while reading." if view.get("hint") or view.get("details") else f"Next exercise in {view.get('remaining', 3)}s. Press a to pause."])
            else:
                lines.extend(["", "Press n when ready to continue."])
        if view.get("hint"):
            lines.extend(["", ruler, "HINT", hint(source), "h or Esc closes this hint."])
        if view.get("notice"):
            lines.extend(["", view['notice']])
        lines.extend(["", "Edit the displayed file; saving runs its tests.", ruler,
                      "[t] learn  [h] hint  [e] edit  [r] run",
                      "[l] learning path  [d] diagnostics",
                      "[n] next after passing  [s] skip  [a] auto  [q] quit"])
    return "\n".join(part for line in lines for paragraph in line.split("\n") for part in (textwrap.wrap(paragraph, width, replace_whitespace=False) or [""]))


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
    global KEY_BUFFER
    if os.name == "nt":
        import msvcrt

        time.sleep(0.1)
        if not msvcrt.kbhit():
            return ""
        key = msvcrt.getwch()
        return {"H": "up", "P": "down", "G": "home", "O": "end"}.get(msvcrt.getwch(), "") if key in ("\x00", "\xe0") else key.lower()
    if not KEY_BUFFER:
        if not select.select([sys.stdin], [], [], 0.1)[0]:
            return ""
        KEY_BUFFER = os.read(sys.stdin.fileno(), 32).decode(errors="replace")
        if not KEY_BUFFER:
            return "q"
    if KEY_BUFFER in ("\x1b", "\x1b[", "\x1bO") and select.select([sys.stdin], [], [], 0.02)[0]:
        KEY_BUFFER += os.read(sys.stdin.fileno(), 32).decode(errors="replace")
    for sequence, key in {"\x1b[A": "up", "\x1b[B": "down", "\x1bOA": "up", "\x1bOB": "down", "\x1b[H": "home", "\x1b[F": "end", "\x1b[1~": "home", "\x1b[4~": "end"}.items():
        if KEY_BUFFER.startswith(sequence):
            KEY_BUFFER = KEY_BUFFER[len(sequence):]
            return key
    unknown = re.match(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|O.)", KEY_BUFFER)
    if unknown:
        KEY_BUFFER = KEY_BUFFER[unknown.end():]
        return ""
    key, KEY_BUFFER = KEY_BUFFER[0], KEY_BUFFER[1:]
    return key.lower()


def wait(passed, automatic, before, view=None, redraw=None):
    view = view if view is not None else {"automatic": automatic}
    deadline = time.monotonic() + 3 if passed and automatic else None
    with keyboard():
        if redraw:
            redraw()
        while True:
            if snapshot() != before:
                return "r"
            key = read_key()
            if key == "q" or (not view.get("list") and key in ("r", "e", "s")):
                return key
            if view.get("list"):
                catalogue = view["catalogue"]
                if key in ("j", "down", "k", "up", "home", "end"):
                    selected = view["selected"]
                    view["selected"] = 0 if key == "home" else len(catalogue) - 1 if key == "end" else max(0, min(len(catalogue) - 1, selected + (1 if key in ("j", "down") else -1)))
                elif key in ("\r", "\n"):
                    view["chosen"] = catalogue[view["selected"]]
                    return "select"
            if key in ("h", "t", "d", "l", "a", "\x1b"):
                if key == "\x1b":
                    view.update(hint=False, learn=False, details=False, list=False)
                else:
                    option = {"h": "hint", "t": "learn", "d": "details", "l": "list", "a": "automatic"}[key]
                    view[option] = not view.get(option, False)
                    if key == "l" and view["list"]:
                        view.setdefault("catalogue", exercises())
                        view["selected"] = view.get("current", 0)
                    if key == "t" and view["learn"]:
                        view.update(hint=False, details=False, list=False)
                    if key in ("h", "d"):
                        view.update(learn=False, list=False)
                deadline = time.monotonic() + 3 if passed and view["automatic"] and not any(view.get(name) for name in ("hint", "learn", "details", "list")) else None
            if passed and key == "n" and not view.get("list"):
                return "n"
            if deadline is not None:
                now = time.monotonic()
                if now >= deadline:
                    return "n"
                view["remaining"] = max(1, int(deadline - now + 0.999))
            if redraw:
                redraw()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--auto", action="store_true", help="advance 3 seconds after tests pass")
    parser.add_argument("--legacy", action="store_true", help="use the original 44-exercise topic order")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto", help="terminal colors (auto respects NO_COLOR)")
    parser.add_argument("--start", metavar="EXERCISE", help="start at an exercise, e.g. variables2")
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build")
    args = parser.parse_args()
    ordered = exercises(args.legacy)
    names = [source.stem for source in ordered]
    progress_names = list(dict.fromkeys(names + [source.stem for source in legacy_exercises()] + [source.stem for source in exercises()]))
    if args.start and args.start not in names:
        parser.error(f"unknown exercise: {args.start}")
    try:
        completed = load_progress(progress_names)
        skipped = load_progress(progress_names, SKIPPED) - completed
    except ValueError as error:
        parser.error(str(error))
    index = names.index(args.start) if args.start else next(
        (i for i, name in enumerate(names) if name not in completed | skipped), len(names)
    )
    if index == len(names):
        print(f"All exercises completed or skipped ({len(skipped)} skipped). Use --start EXERCISE to revisit one.")
        return 0
    build = args.build_dir.resolve()
    print("Configuring CMake...", flush=True)
    configured = subprocess.run(
        ["cmake", "-S", str(ROOT), "-B", str(build), "-DCPLINGS_RUN_TESTS_AFTER_BUILD=OFF"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    if configured.returncode:
        print(configured.stdout)
        return 1
    view = {"automatic": args.auto, "stage": "compile", "status": "running", "skipped": skipped, "catalogue": exercises()}
    last_screen = None

    def redraw():
        nonlocal last_screen
        size = shutil.get_terminal_size()
        output = screen(source, index, ordered, completed, view, size.columns, size.lines)
        if output != last_screen:
            if sys.stdout.isatty() and os.environ.get("TERM") != "dumb":
                print("\x1b[2J\x1b[H", end="")
            use_colour = args.color == "always" or (args.color == "auto" and sys.stdout.isatty() and os.environ.get("TERM") != "dumb" and "NO_COLOR" not in os.environ)
            print(colourize(output) if use_colour else output, flush=True)
            last_screen = output

    def report(stage, status, output):
        view.update(stage=stage, status=status, output=output)
        redraw()

    starting = True
    revisit = bool(args.start)
    while index < len(ordered):
        source = ordered[index]
        if not revisit and source.stem in completed | skipped:
            index += 1
            continue
        view.update(hint=False, learn=False, details=False, list=False, remaining=3, notice="",
                    current=next(i for i, item in enumerate(view['catalogue']) if item.stem == source.stem))
        before = snapshot()
        passed = check(source, build, report=report)
        if passed:
            completed.add(source.stem)
            skipped.discard(source.stem)
        else:
            completed.discard(source.stem)
        save_progress(completed, progress_names)
        save_progress(skipped, progress_names, SKIPPED)
        if starting and passed and not revisit:
            index += 1
            continue
        starting = False
        revisit = False
        while True:
            action = wait(passed, view["automatic"], before, view=view, redraw=redraw)
            if action != "e":
                break
            view['notice'] = edit(source)
            if not view['notice']:
                action = "r"
                break
        if action == "q":
            return 0
        if action == "n":
            index += 1
        elif action == "s":
            completed.discard(source.stem)
            skipped.add(source.stem)
            save_progress(completed, progress_names)
            save_progress(skipped, progress_names, SKIPPED)
            index += 1
        elif action == "select":
            ordered = view['catalogue']
            index = ordered.index(view['chosen'])
            revisit = True
        elif action == "r":
            revisit = True
    print(f"Course finished: {sum(item.stem in completed for item in ordered)} passed, {sum(item.stem in skipped for item in ordered)} skipped. Use --start EXERCISE to revisit.")
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
