"""Run with: python3 -m unittest discover -s tests -p test_sync.py"""

from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

JUSTFILE = Path(__file__).resolve().parents[1] / "justfile"


@unittest.skipUnless(shutil.which("just"), "just is not installed")
class SyncTest(unittest.TestCase):
    def test_only_progress_is_pushed_and_other_device_pulls(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            remote, first, second = (root / name for name in ("remote", "first", "second"))

            def run(*args, cwd=root):
                return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

            def just(recipe, cwd):
                run("just", "--justfile", str(JUSTFILE), "--working-directory", str(cwd), recipe)

            run("git", "init", "--bare", str(remote))
            run("git", "clone", str(remote), str(first))
            run("git", "config", "user.name", "Sync test", cwd=first)
            run("git", "config", "user.email", "sync@example.invalid", cwd=first)
            progress = first / ".cplings-progress.txt"
            skipped = first / ".cplings-skipped.txt"
            solution = first / "exercise.cpp"
            progress.write_text("")
            skipped.write_text("")
            solution.write_text("original exercise\n")
            run("git", "add", ".", cwd=first)
            run("git", "commit", "-m", "Initial exercises", cwd=first)
            run("git", "push", "-u", "origin", "HEAD", cwd=first)
            run("git", "clone", str(remote), str(second))

            progress.write_text("variables1\n")
            solution.write_text("private solution\n")
            run("git", "add", "exercise.cpp", cwd=first)
            just("sync-push", first)
            self.assertEqual(run("git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD", cwd=first), ".cplings-progress.txt")
            self.assertEqual(run("git", "diff", "--cached", "--name-only", cwd=first), "exercise.cpp")
            head = run("git", "rev-parse", "HEAD", cwd=first)
            just("sync-push", first)
            self.assertEqual(run("git", "rev-parse", "HEAD", cwd=first), head)

            skipped.write_text("variables2\n")
            just("sync-push", first)
            self.assertEqual(run("git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD", cwd=first), ".cplings-skipped.txt")

            just("sync-pull", second)
            self.assertEqual((second / ".cplings-progress.txt").read_text(), "variables1\n")
            self.assertEqual((second / ".cplings-skipped.txt").read_text(), "variables2\n")
            self.assertEqual((second / "exercise.cpp").read_text(), "original exercise\n")


if __name__ == "__main__":
    unittest.main()
