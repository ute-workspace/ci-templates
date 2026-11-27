"""Tests for the `attest` input of the container release workflows."""
import os
import pathlib
import subprocess
import tempfile
import unittest

import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
WORKFLOWS = REPO / ".github" / "workflows"
RELEASE_WORKFLOWS = ("container-release.yml", "node-container-release.yml")
IMAGE_REF = "ghcr.io/example/app@sha256:" + "a" * 64


def load(name):
    return yaml.safe_load((WORKFLOWS / name).read_text())


def job_steps(name):
    (job,) = load(name)["jobs"].values()
    return job["steps"]


def step(name, step_name):
    (found,) = [s for s in job_steps(name) if s.get("name") == step_name]
    return found


def run_bash(body, env):
    with tempfile.TemporaryDirectory() as tmp:
        summary = pathlib.Path(tmp) / "summary.md"
        full_env = {"PATH": os.environ["PATH"], "GITHUB_STEP_SUMMARY": str(summary), **env}
        # Same invocation GitHub Actions uses for `shell: bash`.
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", body],
            cwd=tmp, env=full_env, capture_output=True, text=True, check=False,
        )
        return result, summary.read_text() if summary.exists() else ""


class WorkflowShapeTest(unittest.TestCase):
    def test_attest_input_defaults_to_required(self):
        for name in RELEASE_WORKFLOWS:
            with self.subTest(workflow=name):
                # PyYAML reads the `on` key as True.
                attest = load(name)[True]["workflow_call"]["inputs"]["attest"]
                self.assertEqual(attest["default"], "required")
                self.assertEqual(attest["type"], "string")
                self.assertFalse(attest["required"])

    def test_input_is_checked_before_anything_else(self):
        for name in RELEASE_WORKFLOWS:
            with self.subTest(workflow=name):
                first = job_steps(name)[0]
                self.assertEqual(first["name"], "Check attest input")
                self.assertEqual(first["env"]["ATTEST"], "${{ inputs.attest }}")
                self.assertNotIn("inputs.attest", first["run"])

    def test_attest_step_runs_only_when_required_and_can_fail_the_job(self):
        for name in RELEASE_WORKFLOWS:
            with self.subTest(workflow=name):
                attest = step(name, "Attest build provenance")
                self.assertEqual(attest["id"], "attest")
                self.assertEqual(attest["if"], "${{ inputs.attest == 'required' }}")
                self.assertTrue(attest["uses"].startswith("actions/attest-build-provenance@"))
                self.assertNotIn("continue-on-error", attest)
                self.assertEqual(attest["with"]["subject-digest"], "${{ steps.push.outputs.digest }}")

    def test_no_step_ignores_its_failure(self):
        for name in RELEASE_WORKFLOWS:
            with self.subTest(workflow=name):
                self.assertEqual([s for s in job_steps(name) if s.get("continue-on-error")], [])

    def test_report_runs_after_a_push_even_when_attestation_failed(self):
        for name in RELEASE_WORKFLOWS:
            with self.subTest(workflow=name):
                steps = job_steps(name)
                report = step(name, "Report build provenance")
                self.assertEqual(steps[-1], report)
                self.assertEqual(report["if"], "${{ always() && steps.push.outcome == 'success' }}")
                self.assertEqual(report["env"]["ATTEST_OUTCOME"], "${{ steps.attest.outcome }}")
                self.assertEqual(report["env"]["IMAGE_REF"], "${{ steps.image.outputs.ref }}")

    def test_image_ref_output_is_kept(self):
        for name in RELEASE_WORKFLOWS:
            with self.subTest(workflow=name):
                (job,) = load(name)["jobs"].values()
                self.assertEqual(job["outputs"]["image-ref"], "${{ steps.image.outputs.ref }}")

    def test_both_workflows_share_the_same_attestation_steps(self):
        names = ("Check attest input", "Attest build provenance", "Report build provenance")
        first, second = RELEASE_WORKFLOWS
        for step_name in names:
            with self.subTest(step=step_name):
                self.assertEqual(step(first, step_name), step(second, step_name))


class CheckInputTest(unittest.TestCase):
    def run_check(self, value):
        return run_bash(step("container-release.yml", "Check attest input")["run"], {"ATTEST": value})

    def test_accepts_required_and_skip(self):
        for value in ("required", "skip"):
            with self.subTest(value=value):
                result, _ = self.run_check(value)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")

    def test_rejects_other_values_without_echoing_them(self):
        for value in ("", "Required", "false", "skip\n::warning::x", "%0A::error::x"):
            with self.subTest(value=value):
                result, _ = self.run_check(value)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(
                    result.stdout,
                    "::error title=Invalid input::attest must be 'required' or 'skip'\n",
                )


class ReportTest(unittest.TestCase):
    def run_report(self, attest, outcome):
        body = step("container-release.yml", "Report build provenance")["run"]
        return run_bash(body, {"ATTEST": attest, "ATTEST_OUTCOME": outcome, "IMAGE_REF": IMAGE_REF})

    def test_required_and_attested(self):
        result, summary = self.run_report("required", "success")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("::warning", result.stdout)
        self.assertNotIn("::error", result.stdout)
        self.assertIn(f"Attested: `{IMAGE_REF}`", summary)

    def test_skip_is_a_visible_warning_not_a_failure(self):
        result, summary = self.run_report("skip", "skipped")
        self.assertEqual(result.returncode, 0)
        self.assertIn("::warning title=Not attested::", result.stdout)
        self.assertIn("**Not attested** (`attest: skip`)", summary)
        self.assertIn(IMAGE_REF, summary)

    def test_required_but_failed_or_not_run_fails(self):
        for outcome in ("failure", "cancelled", "skipped", ""):
            with self.subTest(outcome=outcome):
                result, summary = self.run_report("required", outcome)
                self.assertEqual(result.returncode, 1)
                self.assertIn("::error title=Attestation failed::", result.stdout)
                self.assertIn("**Attestation failed**", summary)
                self.assertIn("already pushed", summary)
                self.assertNotIn("Attested:", summary)


if __name__ == "__main__":
    unittest.main()
