"""Tests for the copied agent standards warning check and its workflow integration."""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "check-copied-standards.sh"
WORKFLOWS = REPO / ".github" / "workflows"
STEP_NAME = "Check for copied agent standards"
CLEAN_URL = "https://github.com/ute-workspace/agent-standards/blob/main/scripts/clean-project.py"
# Reusable workflow -> directory the caller project is checked out to.
REUSABLE = {
    "node-ci.yml": ".",
    "container-release.yml": ".",
    "node-container-release.yml": ".",
    "ansible-deploy.yml": "caller-project",
    "gitops-image-promotion.yml": "caller-project",
}


def script_body():
    lines = SCRIPT.read_text().splitlines(keepends=True)
    while lines[0].startswith("#"):
        lines.pop(0)
    return "".join(lines)


def run_check(body, cwd, env=None):
    summary = pathlib.Path(cwd) / "summary.md"
    full_env = {"PATH": os.environ["PATH"], "GITHUB_STEP_SUMMARY": str(summary), **(env or {})}
    # Same invocation GitHub Actions uses for `shell: bash`.
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", body],
        cwd=cwd, env=full_env, capture_output=True, text=True, check=False,
    )
    summary_text = summary.read_text() if summary.exists() else ""
    return result, summary_text


def step_env(step, outcome="success"):
    """Step env with the caller checkout outcome expression resolved."""
    env = dict(step.get("env") or {})
    if "CALLER_CHECKOUT_OUTCOME" in env:
        env["CALLER_CHECKOUT_OUTCOME"] = outcome
    return env


def warnings(stdout):
    return [line for line in stdout.splitlines() if line.startswith("::warning ")]


def make(root, *paths):
    for rel in paths:
        target = pathlib.Path(root) / rel
        if rel.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x\n")


class CheckBehaviourTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def check(self, env=None):
        return run_check(script_body(), self.root, env)

    def assert_findings(self, expected):
        result, summary = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        found = warnings(result.stdout)
        self.assertEqual(len(found), len(expected), result.stdout)
        for line, path in zip(found, expected):
            self.assertTrue(line.startswith(f"::warning title=Copied agent standards::{path} "), line)
            self.assertIn(CLEAN_URL, line)
            self.assertIn(f"- <code>{path}</code>", summary)
        self.assertIn(CLEAN_URL, summary)
        self.assertIn("Warning only; the build is not failed.", summary)
        return result, summary

    def test_clean_project_has_no_warnings(self):
        make(self.root, "src/index.js", ".claude/settings.json", ".agents/README.md")
        result, summary = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(warnings(result.stdout), [])
        self.assertIn("No copied agent standards found.", result.stdout)
        self.assertIn("None found.", summary)

    def test_agents_core_directory(self):
        make(self.root, ".agents/core/standards/workflow.md")
        self.assert_findings([".agents/core"])

    def test_agent_standards_marker_file(self):
        make(self.root, ".agent-standards.yml")
        self.assert_findings([".agent-standards.yml"])

    def test_claude_skill_entry(self):
        make(self.root, ".claude/skills/feature-plan/SKILL.md")
        self.assert_findings([".claude/skills/feature-plan"])

    def test_agents_skill_entry(self):
        make(self.root, ".agents/skills/docs-sync/SKILL.md")
        self.assert_findings([".agents/skills/docs-sync"])

    def test_every_skill_entry_is_reported_regardless_of_name(self):
        make(self.root, ".claude/skills/project-own-skill/SKILL.md", ".claude/skills/notes.md")
        self.assert_findings([".claude/skills/notes.md", ".claude/skills/project-own-skill"])

    def test_both_skill_directories(self):
        make(self.root, ".claude/skills/a/SKILL.md", ".claude/skills/b/SKILL.md",
             ".agents/skills/c/SKILL.md", ".agents/skills/d/SKILL.md")
        self.assert_findings([".claude/skills/a", ".claude/skills/b",
                              ".agents/skills/c", ".agents/skills/d"])

    def test_multiple_findings(self):
        make(self.root, ".agents/core/x.md", ".agent-standards.yml",
             ".claude/skills/tdd/SKILL.md", ".agents/skills/tdd/SKILL.md")
        self.assert_findings([".agents/core", ".agent-standards.yml",
                              ".claude/skills/tdd", ".agents/skills/tdd"])

    def test_agents_core_symlink(self):
        os.makedirs(os.path.join(self.root, ".agents"))
        os.symlink("/nonexistent", os.path.join(self.root, ".agents", "core"))
        self.assert_findings([".agents/core"])

    def test_empty_skill_directories_are_clean(self):
        make(self.root, ".claude/skills/", ".agents/skills/")
        result, _ = self.check()
        self.assertEqual(warnings(result.stdout), [])

    def test_annotation_data_is_escaped(self):
        make(self.root, ".claude/skills/bad%0Aname\nnext/")
        result, _ = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        found = warnings(result.stdout)
        self.assertEqual(len(found), 1, result.stdout)
        self.assertIn("bad%250Aname%0Anext", found[0])

    def test_missing_project_checkout_is_a_visible_warning(self):
        result, summary = self.check({"COPIED_STANDARDS_ROOT": "caller-project"})
        self.assertEqual(result.returncode, 0, result.stderr)
        found = warnings(result.stdout)
        self.assertEqual(len(found), 1, result.stdout)
        self.assertIn("not checked", found[0])
        self.assertIn("Not checked", summary)

    def test_failed_checkout_with_existing_directory_is_not_checked(self):
        # A failed checkout can leave a partial or stale directory behind.
        make(self.root, "caller-project/src/index.js")
        for outcome in ("failure", "cancelled", "skipped", ""):
            with self.subTest(outcome=outcome):
                result, summary = self.check({"COPIED_STANDARDS_ROOT": "caller-project",
                                              "CALLER_CHECKOUT_OUTCOME": outcome})
                self.assertEqual(result.returncode, 0, result.stderr)
                found = warnings(result.stdout)
                self.assertEqual(len(found), 1, result.stdout)
                self.assertIn("failed", found[0])
                self.assertIn("not checked", found[0])
                self.assertIn("Not checked", summary)
                self.assertNotIn("None found", summary)
                self.assertNotIn("No copied agent standards found.", result.stdout)
                (pathlib.Path(self.root) / "summary.md").unlink()

    def test_failed_checkout_does_not_report_stale_findings(self):
        make(self.root, "caller-project/.agent-standards.yml")
        result, summary = self.check({"COPIED_STANDARDS_ROOT": "caller-project",
                                      "CALLER_CHECKOUT_OUTCOME": "failure"})
        found = warnings(result.stdout)
        self.assertEqual(len(found), 1, result.stdout)
        self.assertIn("not checked", found[0])
        self.assertNotIn(".agent-standards.yml", summary)

    def test_successful_checkout_outcome_is_inspected(self):
        make(self.root, "caller-project/.agent-standards.yml")
        result, _ = self.check({"COPIED_STANDARDS_ROOT": "caller-project",
                                "CALLER_CHECKOUT_OUTCOME": "success"})
        self.assertEqual(len(warnings(result.stdout)), 1, result.stdout)
        self.assertIn(".agent-standards.yml", result.stdout)

    def test_summary_names_cannot_inject_markdown(self):
        name = "x` [spoof](https://evil.example) <a href=y>`"
        make(self.root, f".claude/skills/{name}/")
        result, summary = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(warnings(result.stdout)), 1, result.stdout)
        entry = [line for line in summary.splitlines() if line.startswith("- ")]
        self.assertEqual(len(entry), 1, summary)
        for raw in ("`", "[", "]", "(", ")", "<a", ">`", "evil.example)"):
            self.assertNotIn(raw, entry[0].removeprefix("- <code>").removesuffix("</code>"))
        self.assertIn("&#91;spoof&#93;&#40;https", entry[0])

    def test_summary_keeps_non_ascii_names(self):
        make(self.root, ".claude/skills/café/")
        _, summary = self.check()
        self.assertIn("- <code>.claude/skills/café</code>", summary)

    def test_regular_file_named_skills(self):
        make(self.root, ".claude/skills", ".agents/skills")
        self.assert_findings([".claude/skills", ".agents/skills"])

    def test_symlinked_skills_directory_is_reported_not_followed(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside)
        make(outside, "outside-name/SKILL.md")
        os.makedirs(os.path.join(self.root, ".claude"))
        os.symlink(outside, os.path.join(self.root, ".claude", "skills"))
        result, summary = self.assert_findings([".claude/skills"])
        self.assertNotIn("outside-name", result.stdout + summary)

    def test_symlinked_parent_is_reported_not_followed(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside)
        make(outside, "skills/outside-name/SKILL.md", "core/x.md")
        os.symlink(outside, os.path.join(self.root, ".claude"))
        os.symlink(outside, os.path.join(self.root, ".agents"))
        result, summary = self.assert_findings([".agents", ".claude"])
        self.assertNotIn("outside-name", result.stdout + summary)

    def test_check_reads_nothing_from_upstream(self):
        body = script_body()
        for forbidden in ("git ", "curl", "wget", "TOKEN", "token", "http://"):
            self.assertNotIn(forbidden, body)
        self.assertEqual(body.count("https://"), 1)


class WorkflowIntegrationTest(unittest.TestCase):
    def steps(self, name):
        workflow = yaml.safe_load((WORKFLOWS / name).read_text())
        (job,) = workflow["jobs"].values()
        return job["steps"]

    def test_every_reusable_workflow_is_covered(self):
        reusable = {p.name for p in WORKFLOWS.glob("*.y*ml")
                    if "workflow_call" in (yaml.safe_load(p.read_text()).get(True) or {})}
        self.assertEqual(reusable, set(REUSABLE))

    def test_embedded_check_matches_script(self):
        for name in REUSABLE:
            with self.subTest(workflow=name):
                (step,) = [s for s in self.steps(name) if s.get("name") == STEP_NAME]
                self.assertEqual(step["run"], script_body())
                self.assertEqual(step.get("shell"), "bash")
                self.assertIs(step.get("continue-on-error"), True)

    def test_check_inspects_caller_checkout(self):
        for name, root in REUSABLE.items():
            with self.subTest(workflow=name):
                steps = self.steps(name)
                index = next(i for i, s in enumerate(steps) if s.get("name") == STEP_NAME)
                check = steps[index]
                env = check.get("env", {})
                self.assertEqual(env.get("COPIED_STANDARDS_ROOT", "."), root)
                checkouts = [s for s in steps[:index]
                             if str(s.get("uses", "")).startswith("actions/checkout@")]
                self.assertTrue(checkouts, "caller checkout must precede the check")
                caller = checkouts[-1].get("with") or {}
                if checkouts[-1].get("continue-on-error"):
                    # The check must see a failed checkout, not just the directory it leaves.
                    self.assertEqual(env.get("CALLER_CHECKOUT_OUTCOME"),
                                     f"${{{{ steps.{checkouts[-1]['id']}.outcome }}}}")
                else:
                    self.assertNotIn("CALLER_CHECKOUT_OUTCOME", env)
                self.assertNotIn("repository", caller)
                self.assertNotIn("token", caller)
                self.assertNotIn("ref", caller)
                self.assertEqual(caller.get("path", "."), root)
                if root != ".":
                    self.assertIs(caller.get("persist-credentials"), False)
                    other_paths = [(s.get("with") or {}).get("path") for s in steps
                                   if s is not checkouts[-1]]
                    self.assertNotIn(root, other_paths)

    def test_embedded_step_warns_and_succeeds(self):
        for name, root in REUSABLE.items():
            with self.subTest(workflow=name), tempfile.TemporaryDirectory() as workspace:
                (step,) = [s for s in self.steps(name) if s.get("name") == STEP_NAME]
                make(os.path.join(workspace, root), ".agent-standards.yml",
                     ".claude/skills/x/SKILL.md")
                # Deployment checkouts beside the caller project are not inspected.
                make(workspace, "gitops/.agent-standards.yml", "ansible/.agents/core/x.md")
                result, summary = run_check(step["run"], workspace, step_env(step))
                self.assertEqual(result.returncode, 0, result.stderr)
                found = warnings(result.stdout)
                self.assertEqual(len(found), 2, result.stdout)
                self.assertIn(".agent-standards.yml", found[0])
                self.assertIn(".claude/skills/x", found[1])
                self.assertIn(CLEAN_URL, summary)

    def test_embedded_step_reports_failed_caller_checkout(self):
        for name, root in REUSABLE.items():
            if root == ".":
                continue
            with self.subTest(workflow=name), tempfile.TemporaryDirectory() as workspace:
                (step,) = [s for s in self.steps(name) if s.get("name") == STEP_NAME]
                make(os.path.join(workspace, root), "src/index.js")
                result, summary = run_check(step["run"], workspace, step_env(step, "failure"))
                self.assertEqual(result.returncode, 0, result.stderr)
                found = warnings(result.stdout)
                self.assertEqual(len(found), 1, result.stdout)
                self.assertIn("not checked", found[0])
                self.assertIn("Not checked", summary)
                self.assertNotIn("None found", summary)


if __name__ == "__main__":
    unittest.main()
