default:
    @just --list

clang_format := env_var_or_default("CLANG_FORMAT", "clang-format-18")

# Format exercise sources, including unfinished exercises.
format:
    {{clang_format}} -i exercises/*/*.cpp

# Check exercise formatting without changing files.
format-check:
    {{clang_format}} --dry-run --Werror exercises/*/*.cpp

# Resume exercises with automatic progression.
run *args:
    python3 cplings.py --auto {{args}}

# Sync completed and skipped names without exercise solutions.
sync-push:
    @if ! git diff --quiet HEAD -- .cplings-progress.txt .cplings-skipped.txt; then git commit --only -m "Save exercise progress" -- .cplings-progress.txt .cplings-skipped.txt; fi
    git push

# Get progress from the other device without creating a merge commit.
sync-pull:
    git pull --ff-only
