"""Run with: python3 -m unittest discover -s tests -p test_runner.py"""

from contextlib import nullcontext
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cplings


class RunnerTest(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        progress = patch("cplings.PROGRESS", Path(directory.name) / ".cplings-progress.txt")
        progress.start()
        self.addCleanup(progress.stop)

    def test_order_matches_existing_targets(self):
        ordered = cplings.exercises()
        self.assertEqual(len(ordered), 44)
        self.assertEqual(ordered[0].stem, "variables1")
        self.assertEqual(ordered[-1].stem, "security4")
        self.assertTrue(all(source.is_file() for source in ordered))

    def test_build_and_runtime_failures(self):
        source = cplings.exercises()[0]
        build = cplings.ROOT / "build"
        with patch("cplings.subprocess.run") as run, patch.object(Path, "exists", return_value=True):
            run.return_value.returncode = 1
            self.assertFalse(cplings.check(source, build))
            self.assertEqual(run.call_count, 1)
            run.reset_mock()
            run.side_effect = [Mock(returncode=0), Mock(returncode=1)]
            self.assertFalse(cplings.check(source, build))
            run.side_effect = [Mock(returncode=0), Mock(returncode=0)]
            self.assertTrue(cplings.check(source, build))
            self.assertEqual(run.call_args.args[0], [str(build / "exercises/01_variables/variables1")])

    def test_progression(self):
        with patch("cplings.keyboard", return_value=nullcontext()), patch("cplings.snapshot", return_value={}), patch("cplings.print"):
            with patch("cplings.read_key", side_effect=["n", "q"]):
                self.assertEqual(cplings.wait(False, True, {}), "q")
            with patch("cplings.read_key", return_value="n"):
                self.assertEqual(cplings.wait(True, False, {}), "n")
            with patch("cplings.read_key", return_value=""), patch("cplings.time.monotonic", side_effect=[10, 12.9, 13]):
                self.assertEqual(cplings.wait(True, True, {}), "n")
            with patch("cplings.snapshot", return_value={"edited": 1}):
                self.assertEqual(cplings.wait(True, True, {}), "r")
            with patch("cplings.read_key", return_value="r"):
                self.assertEqual(cplings.wait(False, False, {}), "r")

    def test_main_retries_then_advances(self):
        ordered = cplings.exercises()[:2]
        with patch.object(sys, "argv", ["cplings.py", "--auto"]), patch("cplings.exercises", return_value=ordered), patch("cplings.subprocess.run", return_value=Mock(returncode=0)), patch("cplings.snapshot", return_value={}), patch("cplings.check", side_effect=[False, True, True]) as check, patch("cplings.wait", side_effect=["r", "n", "n"]) as wait, patch("cplings.print"):
            self.assertEqual(cplings.main(), 0)
            self.assertEqual([call.args[0] for call in check.call_args_list], [ordered[0], ordered[0], ordered[1]])
            self.assertEqual([call.args[:2] for call in wait.call_args_list], [(False, True), (True, True), (True, True)])

    def test_startup_skips_passed_exercises(self):
        ordered = cplings.exercises()[:3]
        for options in ([], ["--auto"]):
            cplings.PROGRESS.unlink(missing_ok=True)
            with self.subTest(options=options), patch.object(sys, "argv", ["cplings.py", *options]), patch("cplings.exercises", return_value=ordered), patch("cplings.subprocess.run", return_value=Mock(returncode=0)), patch("cplings.snapshot", return_value={}), patch("cplings.check", side_effect=[True, True, False, True]) as check, patch("cplings.wait", side_effect=["r", "n"]) as wait, patch("cplings.print"):
                self.assertEqual(cplings.main(), 0)
                self.assertEqual([call.args[0] for call in check.call_args_list], [*ordered, ordered[-1]])
                self.assertEqual([call.args[:2] for call in wait.call_args_list], [(False, bool(options)), (True, bool(options))])
        cplings.PROGRESS.unlink(missing_ok=True)
        with patch.object(sys, "argv", ["cplings.py", "--auto"]), patch("cplings.exercises", return_value=ordered), patch("cplings.subprocess.run", return_value=Mock(returncode=0)), patch("cplings.snapshot", return_value={}), patch("cplings.check", return_value=True), patch("cplings.wait") as wait, patch("cplings.print"):
            self.assertEqual(cplings.main(), 0)
            wait.assert_not_called()

    def test_progress_round_trip_and_validation(self):
        names = ["variables1", "variables2", "variables3"]
        self.assertEqual(cplings.load_progress(names), set())
        cplings.save_progress({"variables2", "variables1"}, names)
        self.assertEqual(cplings.PROGRESS.read_text(), "variables1\nvariables2\n")
        self.assertEqual(cplings.load_progress(names), {"variables1", "variables2"})
        self.assertFalse(cplings.PROGRESS.with_suffix(".tmp").exists())
        cplings.PROGRESS.write_text("not_an_exercise\n")
        with self.assertRaises(ValueError):
            cplings.load_progress(names)
        self.assertEqual(cplings.PROGRESS.read_text(), "not_an_exercise\n")

    def test_resume_without_solutions_and_explicit_recheck(self):
        ordered = cplings.exercises()[:3]
        names = [source.stem for source in ordered]
        cplings.save_progress(set(names[:2]), names)
        for options, expected in (([], ordered[2]), (["--start", names[0]], ordered[0])):
            with self.subTest(options=options), patch.object(sys, "argv", ["cplings.py", *options]), patch("cplings.exercises", return_value=ordered), patch("cplings.subprocess.run", return_value=Mock(returncode=0)), patch("cplings.snapshot", return_value={}), patch("cplings.check", return_value=False) as check, patch("cplings.wait", return_value="q"), patch("cplings.print"):
                self.assertEqual(cplings.main(), 0)
                self.assertEqual(check.call_args.args[0], expected)
                self.assertEqual(check.call_count, 1)
        self.assertEqual(cplings.load_progress(names), {names[1]})

    def test_all_completed_needs_no_build(self):
        ordered = cplings.exercises()[:2]
        names = [source.stem for source in ordered]
        cplings.save_progress(set(names), names)
        with patch.object(sys, "argv", ["cplings.py"]), patch("cplings.exercises", return_value=ordered), patch("cplings.subprocess.run") as run, patch("cplings.print"):
            self.assertEqual(cplings.main(), 0)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
