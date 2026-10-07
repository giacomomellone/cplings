![C++ Logo](https://upload.wikimedia.org/wikipedia/commons/1/18/ISO_C%2B%2B_Logo.svg?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original)

# cplings C++❤️

Greetings and welcome to `cplings`. This project contains small exercises to get you used to reading and writing C++ code. This includes reading and responding to compiler messages!

Alternatively, for a first-time C++ learner, there are several other resources:

- [learncpp.com](https://www.learncpp.com/) - The most comprehensive resource for learning C++, but a bit theoretical sometimes. You will be using this along with cplings!
- [A Tour of C++, from Bjarne Stroustrup](https://isocpp.org/tour) - Learn C++ by solving little exercises! It's almost like `cplings`, but online
- [The C++ FAQ](https://isocpp.org/wiki/faq)
- [C++ Core guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)

*cplings got its inspiration from the magnificient [rustlings repository](https://github.com/rust-lang/rustlings), which aims at familiarizing newcomers to the Rust language. This repository is a sort of a fork of it but for the C++ language*


## Getting Started

You will need to have a C++ Compiler installed. You can get it by following the instructions below.

Install and Usage Demo video:

[![Install and Usage Demo](https://img.youtube.com/vi/18vNfxwU5n4/0.jpg)](https://youtu.be/18vNfxwU5n4)

## Windows
Visit https://visualstudio.microsoft.com/vs/community/ and download Visual Studio Community.
When, installing it make sure to select Desktop development with C++ and then, in the "Installation details" menu enable support for the C++ CMake Tools for Windows

## Linux

For Ubuntu:

```sh
sudo apt install g++ cmake make gdb git libasan8
```

For Fedora:

```sh
sudo dnf install gcc-c++ cmake make gdb git libasan
```

Clone this repository and build:
```sh
git clone https://github.com/rdjondo/cplings
cd cplings
cmake . -B build
cmake --build build --parallel $(nproc)
```

You should expect the build to fail : your task is to fix each exercise for the build to succed.

## Windows
Install Visual Studio Community Edition and Git.

```cmd
# Clone this repository
git clone https://github.com/rdjondo/cplings

```

Open the folder cplings in Visual Studio. Add support for CMake and run a build. You should expect the build to fail : your task is to fix each exercise for the build to succed.


## Doing the exercises

The exercises are sorted by topic and can be found in the subdirectory `cplings/exercises/<topic>`. Press `t` in the runner for a concept explanation and a question to answer before editing. Topic README files provide additional resources where available.

The task is simple. Most exercises contain an error that keeps them from compiling, and it's up to you to fix it! Some exercises are also run as tests, but cplings handles them all the same. To run the exercises in the recommended order, execute:

### In Linux
For an interactive runner (Python 3 and CMake required), run from the repository:

```sh
just              # List the commands
just run          # Start or resume the complete terminal course
```

Without `just`, use `python3 cplings.py --auto`.

The runner builds and runs the tests for all 71 exercises one at a time, sorted
by topic folder and filename: `variables1` through `variables8`, then `functions1`
through `functions6`, and so on, regardless of difficulty. It resumes at the first exercise not recorded as completed in
`.cplings-progress.txt` or skipped in `.cplings-skipped.txt`. On startup, other passing exercises are advanced through
immediately until the first failure. Edit the displayed file in your editor; saving a change triggers
another check. The minimal terminal screen shows the current test and its result.
Press `t` to learn the concept, `h` for a hint, `e` to open the exercise in
`$VISUAL` or `$EDITOR` (defaults to `vi`), and `d` for full diagnostics.
Press `l` for the course list: arrows or `j`/`k` select an exercise and Enter
starts it, including completed or skipped exercises. Home/End jump to the ends.
Press `n` after passing, `s` to mark the current exercise skipped and continue,
`r` to retry, or `q` to quit.
Press `a` to toggle automatic mode; learning text, hints, diagnostics, and the list pause its
countdown. Esc closes those views. In `--auto` mode, passing tests advance after three seconds. A failed build
or test keeps you on the current exercise. Ctrl+C also quits.

Failures are red, passes green, running stages blue, hints yellow, and shortcuts
cyan. Colors are automatic in a terminal and respect `NO_COLOR`. Use
`just run --color always` to override that setting, or `--color never` for plain
text. Redirected output is plain text unless colors are explicitly forced.

Use `--start variables2` to start at a particular exercise, or
`--build-dir /path/to/build` to use another build directory. On Windows, use
`python cplings.py` with Python 3 and CMake available in your terminal.

### Learning path

`learning_path.json` groups lessons by difficulty and supplies their learning text
and hints; it does not determine the runner's order. Every lesson has learning
text with `t` and a hint with `h`. Read the objective,
predict the result, make your change, and explain why the tests now pass.

| Level | Lessons | Focus |
| --- | ---: | --- |
| Easy | 19 | Variables, functions, branches, references, const borrowing, boundaries, map lookup |
| Moderate | 15 | Classes, containers, RAII, unique ownership, captures, algorithms, optional |
| Intermediate | 17 | Templates, dispatch, returned lifetimes, move capture, span, unwinding, expected, joining |
| Hard | 14 | Const and moves, invalidation, weak ownership, concepts, atomics, exception guarantees, security |
| Difficult | 6 | Escaping callbacks, rollback, shutdown, cancellation, generic composition, combined safety audit |

All 71 exercises live under `exercises/<topic>/`, including the 27 new lessons.
Difficulty is a comment in each source file and appears in the runner; it does
not determine the folder. The new lessons supply the test harness,
so most fixes need only 1–5 lines. Concurrency tests use synchronization instead
of sleeps. AddressSanitizer exposes the deliberately dangling memory in lifetime
lessons; hanging tests stop after 30 seconds. Use a C++23 compiler and standard
library supporting `std::expected` (the path was checked with GCC 13).

The original 44 exercises and the 27 new lessons form one course. Use
`just run --start variables8` to revisit any exercise, or select it with `l`.
`--legacy` remains available for compatibility with the old 44-exercise order.
Exercise identifiers stay unchanged, so existing progress remains valid.

Skipped exercises appear as `skipped` in the list and are passed over on resume.
They are not counted as completed. Select one to revisit it; passing its tests
moves it from skipped to completed.

The runner captures build output, runs each exercise's tests once, and stops a
test after 30 seconds if it hangs. It configures the selected build directory
with `CPLINGS_RUN_TESTS_AFTER_BUILD=OFF` so compile errors and test failures stay
separate. To restore tests during standalone builds in that directory, run
`cmake -S . -B build -DCPLINGS_RUN_TESTS_AFTER_BUILD=ON`.

### Sync progress between devices

With `just` installed, use `just sync-pull` before a session, `just run` to
resume with automatic progression, and `just sync-push` when finished.
`sync-push` commits only `.cplings-progress.txt` and `.cplings-skipped.txt`,
even if other files are staged,
and pushes to your branch's configured remote. If progress is unchanged, it
skips the commit and still pushes. Run `just` to list the commands.

The runner saves completed exercise names in `.cplings-progress.txt` whenever it
checks an exercise. Both progress files contain names only, with no solution code. After quitting the runner,
commit and push **only these files** to your fork:

```sh
git add .cplings-progress.txt .cplings-skipped.txt
git commit -m "Save exercise progress"
git push
```

On another device, clone your fork (or run `git pull --ff-only` in an existing
clone), then start the runner:

```sh
git clone https://github.com/giacomomellone/cplings
cd cplings
python3 cplings.py --auto
```

Previously completed exercises are skipped even though their source files in the
new clone still contain the original exercises. `--start variables2` explicitly
rechecks an earlier exercise and updates its completion status. Unfinished code
and solution files remain local; this sync carries your place, not your code.
Pull before starting a session on another device and push progress when finished.
If Git reports a progress-file conflict, keep the union of names in each file,
one per line; completion takes precedence over skipping. Exercise files are tracked, so `git add .` would also stage
your solutions: use the explicit filename above instead.

To run all exercises in predetermined order:

```sh
cd build
make
```

This will try to verify the completion of every exercise in a predetermined order (what we think is best for newcomers).

OR, to run a specific exercise, tell make with exercise to run. For example:

```bash
make variables2
```

### In Windows
Visual Studio will let you choose the specific exercise you would like to solve.

## Hints
Press `h` in the terminal. The runner reads an existing hint file when present,
otherwise the conceptual hint from `learning_path.json`. Press `t` for the
learning explanation and prediction question.

## Continuing On

Once you've completed cplings, put your new knowledge to good use! Continue practicing your C++ skills by building your own projects, contributing to cplings, or finding other open-source projects to contribute to.


## Uninstalling cplings

If you'd like to uninstall cplings, you can do so by simply deleting the cplings directory.

Now you should be done!


## Completion

cplings isn't done and could still be improved.
- More hints
- Structs and Classes
- Better ownership stuff
- Better safer programming, security stuff
- Threads
- Metaprogramming
- ??? probably more

If you are interested in improving or adding new ones, please feel free to contribute!

## Contributing

Contributions of any kind welcome!

Exercise sources use clang-format 18 with the repository's `.clang-format`
configuration (four spaces per indentation level, no tabs). On Ubuntu, install it with
`sudo apt install clang-format-18`, then run:

```sh
just format        # Format all exercise sources
just format-check  # Check formatting without changing files
```

Without `just`, run `clang-format-18 -i exercises/*/*.cpp` or
`clang-format-18 --dry-run --Werror exercises/*/*.cpp`. If your clang-format 18
binary has another name, use `CLANG_FORMAT=clang-format just format`.
Formatting works on the deliberately unfinished exercises and preserves their
teaching comments and include order. CI checks the exercise formatting on every
push and pull request.


## Some technical notes

The cpling build system based on CMake and [CPM.make](https://github.com/cpm-cmake/CPM.cmake) for package management

### How to use cmake
https://cliutils.gitlab.io/modern-cmake/
