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
        skipped = patch("cplings.SKIPPED", Path(directory.name) / ".cplings-skipped.txt")
        skipped.start()
        self.addCleanup(skipped.stop)
        buffer = patch("cplings.KEY_BUFFER", "")
        buffer.start()
        self.addCleanup(buffer.stop)

    def test_order_matches_existing_targets(self):
        ordered = cplings.exercises(legacy=True)
        self.assertEqual(len(ordered), 44)
        self.assertEqual(ordered[0].stem, "variables1")
        self.assertEqual(ordered[-1].stem, "security4")
        self.assertTrue(all(source.is_file() for source in ordered))

    def test_default_order_follows_topics_and_filenames_across_difficulties(self):
        ordered = cplings.exercises()
        names = [source.stem for source in ordered]
        self.assertEqual(names[:14],
                         [f"variables{i}" for i in range(1, 9)] +
                         [f"functions{i}" for i in range(1, 7)])
        topics = [source.parent.name for source in ordered]
        self.assertEqual(topics, sorted(topics))
        for topic in set(topics):
            filenames = [source.name for source in ordered if source.parent.name == topic]
            self.assertEqual(filenames, sorted(filenames))
        self.assertEqual(len(ordered), 71)
        self.assertEqual(set(ordered), {cplings.ROOT / item['path'] for item in cplings.lessons()})
        self.assertGreater(cplings.lesson(ordered[7])['rank'], cplings.lesson(ordered[8])['rank'])

    def test_learning_path_has_increasing_levels_and_hints(self):
        lessons = cplings.lessons()
        self.assertEqual(len(lessons), 71)
        self.assertEqual(len({item['name'] for item in lessons}), 71)
        self.assertEqual([item['rank'] for item in lessons], sorted(item['rank'] for item in lessons))
        self.assertEqual({item['rank'] for item in lessons}, {1, 2, 3, 4, 5})
        for item in lessons:
            source = cplings.ROOT / item['path']
            self.assertTrue(source.is_file())
            self.assertEqual(source.stem, item['name'])
            self.assertTrue(cplings.hint(source))
            self.assertTrue(item['objective'])
            self.assertTrue(item['learn'])
            self.assertTrue(item['question'])
            self.assertIn(f"// Difficulty: {item['level']} ({item['rank']}/5)", source.read_text())
            self.assertEqual(source.parent.parent, cplings.ROOT / 'exercises')
        self.assertEqual(set(cplings.exercises()), set((cplings.ROOT / 'exercises').rglob('*.cpp')))

    def test_colour_preserves_text_and_highlights_states(self):
        import re
        text = 'cplings    0/34 completed\n[compile] FAILED\n[test] PASSED\n[test] RUNNING\nHINT\n[h] hint  [q] quit'
        coloured = cplings.colourize(text)
        self.assertEqual(re.sub(r'\x1b\[[0-9;]*m', '', coloured), text)
        for colour, label in [('31;1', '[compile] FAILED'), ('32;1', '[test] PASSED'), ('34;1', '[test] RUNNING'), ('33;1', 'HINT'), ('36;1', '[h]')]:
            self.assertIn(f'\x1b[{colour}m{label}', coloured)

    def test_colour_modes_and_no_color(self):
        def failed_check(source, build, report):
            report('compile', 'failed', 'error: example')
            return False

        for mode, no_color, tty, expected in [('auto', False, True, True), ('auto', True, True, False), ('auto', False, False, False), ('always', True, True, True), ('never', False, True, False)]:
            with self.subTest(mode=mode, no_color=no_color, tty=tty), patch.object(sys, 'argv', ['cplings.py', '--color', mode]), patch.dict(cplings.os.environ, {'TERM': 'xterm-256color'}, clear=True), patch('cplings.sys.stdout.isatty', return_value=tty), patch('cplings.subprocess.run', return_value=Mock(returncode=0)), patch('cplings.snapshot', return_value={}), patch('cplings.check', side_effect=failed_check), patch('cplings.wait', return_value='q'), patch('cplings.print'), patch('cplings.colourize', wraps=cplings.colourize) as coloured:
                if no_color:
                    cplings.os.environ['NO_COLOR'] = '1'
                self.assertEqual(cplings.main(), 0)
                self.assertEqual(coloured.called, expected)

    def test_new_path_preserves_completed_legacy_exercises(self):
        cplings.PROGRESS.write_text('variables4\nvariables8\n')
        with patch.object(sys, 'argv', ['cplings.py']), patch('cplings.subprocess.run', return_value=Mock(returncode=0)), patch('cplings.snapshot', return_value={}), patch('cplings.check', return_value=False), patch('cplings.wait', return_value='q'), patch('cplings.print'):
            self.assertEqual(cplings.main(), 0)
        self.assertEqual(set(cplings.PROGRESS.read_text().splitlines()), {'variables4', 'variables8'})
        view = {'automatic': False, 'stage': 'compile', 'status': 'failed'}
        self.assertIn('2/71 completed', cplings.screen(cplings.exercises()[0], 0, cplings.exercises(), {'variables4', 'variables8'}, view))

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
            self.assertEqual(run.call_args.args[0], [str(build / "exercises/01_variables/variables1"), "--colour-mode", "none"])

    def test_compile_test_and_timeout_are_distinct(self):
        source = cplings.exercises()[0]
        report = Mock()
        with patch("cplings.subprocess.run", side_effect=[Mock(returncode=0, stdout="built"), Mock(returncode=1, stdout="FAILED: assertion")]), patch.object(Path, "exists", return_value=True):
            self.assertFalse(cplings.check(source, cplings.ROOT / "build", report))
            self.assertEqual([call.args[:2] for call in report.call_args_list], [("compile", "running"), ("test", "running"), ("test", "failed")])
        report.reset_mock()
        with patch("cplings.subprocess.run", side_effect=[Mock(returncode=0, stdout="built"), cplings.subprocess.TimeoutExpired("test", 30, output=b"partial output")]), patch.object(Path, "exists", return_value=True):
            self.assertFalse(cplings.check(source, cplings.ROOT / "build", report))
            self.assertEqual(report.call_args.args[:2], ("test", "timeout"))
            self.assertIn("partial output", report.call_args.args[2])

    def test_minimal_screen_and_hints(self):
        ordered = cplings.exercises(legacy=True)
        source = ordered[8]
        view = {"automatic": False, "stage": "compile", "status": "failed", "output": "[98%] Built target Catch2\nfunctions1.cpp:12:3: error: missing callme\n  callme();\n"}
        output = cplings.screen(source, 8, ordered, set(), view, 60)
        self.assertIn("TEST  identity_function", output)
        self.assertIn("[test] NOT RUN", output)
        self.assertIn("error: missing callme", output)
        self.assertTrue(all(len(line) <= 60 for line in output.splitlines()))
        self.assertIn("define a new function", cplings.hint(source))
        self.assertTrue(cplings.hint(ordered[9]))
        view["hint"] = True
        self.assertIn("HINT", cplings.screen(source, 8, ordered, set(), view))
        view["list"] = True
        view["selected"] = len(ordered) - 1
        self.assertIn("security4", cplings.screen(source, 8, ordered, set(), view))

    def test_course_navigation_and_learning_pause_auto(self):
        view = {'automatic': True, 'current': 0, 'catalogue': cplings.exercises()}
        with patch('cplings.keyboard', return_value=nullcontext()), patch('cplings.snapshot', return_value={}), patch('cplings.read_key', side_effect=['l', 'down', '\n']), patch('cplings.time.monotonic', return_value=10):
            self.assertEqual(cplings.wait(True, True, {}, view), 'select')
        self.assertEqual(view['chosen'], cplings.exercises()[1])
        with patch('cplings.keyboard', return_value=nullcontext()), patch('cplings.snapshot', return_value={}), patch('cplings.read_key', side_effect=['t', '', 'q']), patch('cplings.time.monotonic', side_effect=[10]):
            self.assertEqual(cplings.wait(True, True, {}, view), 'q')
        self.assertTrue(view['learn'])
        self.assertFalse(view['list'])

    def test_list_scrolls_and_shows_skipped(self):
        ordered = cplings.exercises()
        view = {'automatic': False, 'list': True, 'selected': len(ordered)-1, 'skipped': {ordered[-1].stem}}
        output = cplings.screen(ordered[0], 0, ordered, set(), view, 80, 24)
        self.assertIn('skipped', output)
        self.assertIn(ordered[-1].stem, output)
        self.assertLessEqual(len(output.splitlines()), 24)
        self.assertTrue(all(len(line) <= 80 for line in output.splitlines()))

    def test_arrows_preserve_following_input_and_escape(self):
        with patch('cplings.select.select', return_value=([sys.stdin], [], [])), patch('cplings.os.read', return_value=b'\x1b[Bq'):
            self.assertEqual(cplings.read_key(), 'down')
            self.assertEqual(cplings.read_key(), 'q')
        cplings.KEY_BUFFER = '\x1bq'
        self.assertEqual(cplings.read_key(), '\x1b')
        self.assertEqual(cplings.read_key(), 'q')
        with patch('cplings.select.select', return_value=([sys.stdin], [], [])), patch('cplings.os.read', side_effect=[b'\x1b[', b'Aq']):
            self.assertEqual(cplings.read_key(), 'up')
            self.assertEqual(cplings.read_key(), 'q')

    def test_editor_command_uses_arguments_without_a_shell(self):
        with patch.dict(cplings.os.environ, {'VISUAL': 'editor --wait'}, clear=True), patch('cplings.subprocess.run', return_value=Mock(returncode=0)) as run:
            self.assertIsNone(cplings.edit(cplings.exercises()[0]))
        self.assertEqual(run.call_args.args[0], ['editor', '--wait', str(cplings.exercises()[0])])

    def test_skip_is_persisted_and_does_not_block_later_exercises(self):
        ordered = cplings.exercises()[:3]
        with patch.object(sys, 'argv', ['cplings.py']), patch('cplings.exercises', return_value=ordered), patch('cplings.subprocess.run', return_value=Mock(returncode=0)), patch('cplings.snapshot', return_value={}), patch('cplings.check', side_effect=[False, False, True]), patch('cplings.wait', side_effect=['s', 's', 'n']), patch('cplings.print'):
            self.assertEqual(cplings.main(), 0)
        self.assertEqual(cplings.load_progress([item.stem for item in ordered], cplings.SKIPPED), {item.stem for item in ordered[:2]})
        self.assertEqual(cplings.load_progress([item.stem for item in ordered]), {ordered[2].stem})
        cplings.PROGRESS.write_text('')
        with patch.object(sys, 'argv', ['cplings.py']), patch('cplings.exercises', return_value=ordered), patch('cplings.subprocess.run', return_value=Mock(returncode=0)), patch('cplings.snapshot', return_value={}), patch('cplings.check', return_value=False) as check, patch('cplings.wait', return_value='q'), patch('cplings.print'):
            self.assertEqual(cplings.main(), 0)
            self.assertEqual(check.call_args.args[0], ordered[2])

    def test_select_revisits_completed_and_passing_unskips(self):
        ordered = cplings.exercises()[:2]
        names = [item.stem for item in ordered]
        cplings.save_progress({names[0]}, names)
        def select(passed, automatic, before, view, redraw):
            view['chosen'] = ordered[0]
            return 'select'
        with patch.object(sys, 'argv', ['cplings.py']), patch('cplings.exercises', return_value=ordered), patch('cplings.subprocess.run', return_value=Mock(returncode=0)), patch('cplings.snapshot', return_value={}), patch('cplings.check', side_effect=[False, True]) as check, patch('cplings.wait', side_effect=[select, 'q']) as wait, patch('cplings.print'):
            wait.side_effect = lambda *args, **kwargs: select(*args, **kwargs) if kwargs['view']['current'] == 1 else 'q'
            self.assertEqual(cplings.main(), 0)
            self.assertEqual([call.args[0] for call in check.call_args_list], [ordered[1], ordered[0]])
        cplings.save_progress({names[1]}, names, cplings.SKIPPED)
        with patch.object(sys, 'argv', ['cplings.py', '--start', names[1]]), patch('cplings.exercises', return_value=ordered), patch('cplings.subprocess.run', return_value=Mock(returncode=0)), patch('cplings.snapshot', return_value={}), patch('cplings.check', return_value=True), patch('cplings.wait', return_value='q'), patch('cplings.print'):
            self.assertEqual(cplings.main(), 0)
        self.assertEqual(cplings.load_progress(names, cplings.SKIPPED), set())

    def test_hint_pauses_automatic_advance(self):
        view = {"automatic": True}
        with patch("cplings.keyboard", return_value=nullcontext()), patch("cplings.snapshot", return_value={}), patch("cplings.read_key", side_effect=["h", "", "q"]), patch("cplings.time.monotonic", side_effect=[10]):
            self.assertEqual(cplings.wait(True, True, {}, view=view), "q")
        self.assertTrue(view["hint"])
        view = {"automatic": False}
        with patch("cplings.keyboard", return_value=nullcontext()), patch("cplings.snapshot", return_value={}), patch("cplings.read_key", side_effect=["a", "", ""]), patch("cplings.time.monotonic", side_effect=[10, 12, 12.9, 13]):
            self.assertEqual(cplings.wait(True, False, {}, view=view), "n")
        self.assertTrue(view["automatic"])

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

    def test_retry_after_passing_rechecks_the_same_exercise(self):
        ordered = cplings.exercises()[:2]
        with patch.object(sys, 'argv', ['cplings.py', '--start', ordered[0].stem]), patch('cplings.exercises', return_value=ordered), patch('cplings.subprocess.run', return_value=Mock(returncode=0)), patch('cplings.snapshot', return_value={}), patch('cplings.check', side_effect=[True, False]) as check, patch('cplings.wait', side_effect=['r', 'q']), patch('cplings.print'):
            self.assertEqual(cplings.main(), 0)
            self.assertEqual([call.args[0] for call in check.call_args_list], [ordered[0], ordered[0]])
        self.assertEqual(cplings.PROGRESS.read_text(), '')

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
