#!/usr/bin/env python3
"""Exercise the installed command boundary with a disposable Canvas launcher."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SK = Path(__file__).resolve().with_name("sk")


class WorkspaceBridgeTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="shotkit-workspace-test-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.project = self.root / "Project with spaces & notes"
        self.output = self.project / "output"
        self.output.mkdir(parents=True)
        (self.output / "run.json").write_text('{"run_id":"demo-run"}')
        (self.output / "shots.json").write_text('{"shots":[{"id":"shot_01"}]}')
        self.runtime = self.root / "Canvas runtime"
        self.runtime.mkdir()
        (self.runtime / "serve.py").touch()
        self.workspace_api = self.runtime / "WORKSPACE_API"
        self.workspace_api.write_text("1\n")
        self.receipt = self.root / "launch.json"
        self.env = dict(os.environ, SHOTKIT_TEST_LAUNCH_RECEIPT=str(self.receipt))
        self.env.pop("SHOTKIT_CANVAS_HOME", None)
        launcher = self.runtime / "start.sh"
        launcher.write_text(
            '#!/usr/bin/env python3\n'
            'import json, os, pathlib, sys\n'
            'pathlib.Path(os.environ["SHOTKIT_TEST_LAUNCH_RECEIPT"]).write_text(\n'
            '    json.dumps(dict(args=sys.argv[1:], cwd=os.getcwd(), pid=os.getpid())))\n'
        )
        launcher.chmod(0o755)

    def command(self, *args):
        return subprocess.run(
            [str(SK), "workspace", *map(str, args)],
            cwd=self.root, env=self.env, text=True, capture_output=True, check=False,
        )

    def test_project_and_output_open_the_same_run(self):
        for path in (self.project, self.output.relative_to(self.root)):
            with self.subTest(path=path):
                result = self.command(path, "--runtime", self.runtime, "--port", 0, "--rules-only", "--open")
                self.assertEqual(result.returncode, 0, result.stderr)
                args = json.loads(self.receipt.read_text())
                self.assertEqual(args["cwd"], str(self.runtime.resolve()))
                self.assertEqual(args["args"], [str(self.project.resolve()), "--port", "0", "--rules-only", "--open"])

    def test_explicit_runtime_precedes_environment(self):
        self.env["SHOTKIT_CANVAS_HOME"] = str(self.root / "missing runtime")
        result = self.command(self.project, "--runtime", self.runtime)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_workspace_loads_flat_runs_using_the_configured_runtime(self):
        standalone = self.root / "standalone run"
        self.output.rename(standalone)
        self.env["SHOTKIT_CANVAS_HOME"] = str(self.runtime)
        result = self.command(standalone)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.receipt.read_text())["args"], [str(standalone.resolve())])

    def test_missing_runtime_suggests_setup_and_the_portable_board(self):
        result = self.command(self.project)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SHOTKIT_CANVAS_HOME", result.stderr)
        self.assertIn("sk board", result.stderr)
        self.assertFalse(self.receipt.exists())

    def test_invalid_run_is_rejected_before_launch(self):
        result = self.command(self.root, "--runtime", self.runtime)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("shots.json", result.stderr)
        self.assertFalse(self.receipt.exists())

    def test_incompatible_canvas_rejects_launch(self):
        self.workspace_api.write_text("0\n")
        result = self.command(self.project, "--runtime", self.runtime)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("workspace API 1", result.stderr)
        self.assertFalse(self.receipt.exists())

    def test_invalid_port_is_rejected_before_launch(self):
        result = self.command(self.project, "--runtime", self.runtime, "--port", 65536)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("65535", result.stderr)
        self.assertFalse(self.receipt.exists())

    def test_canvas_replaces_cli_process(self):
        # The process an operator stops must be the one running the workspace.
        with subprocess.Popen(
            [str(SK), "workspace", str(self.project), "--runtime", str(self.runtime)],
            cwd=self.root, env=self.env, text=True, stderr=subprocess.PIPE,
        ) as process:
            _, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(json.loads(self.receipt.read_text())["pid"], process.pid)

    def test_isolated_mode_is_forwarded(self):
        result = self.command(self.project, "--runtime", self.runtime, "--isolated")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.receipt.read_text())["args"], [str(self.project.resolve()), "--isolated"])


if __name__ == "__main__":
    unittest.main()
