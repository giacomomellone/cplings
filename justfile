default:
    @just --list

# Resume exercises with automatic progression.
run:
    python3 cplings.py --auto

# Commit only progress, then push to the branch's configured remote.
sync-push:
    @if ! git diff --quiet HEAD -- .cplings-progress.txt; then git commit --only -m "Save exercise progress" -- .cplings-progress.txt; fi
    git push

# Get progress from the other device without creating a merge commit.
sync-pull:
    git pull --ff-only
