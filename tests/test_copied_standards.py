"""Tests for the copied agent standards check and its workflow integration."""
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


def workflow_steps(name):
    workflow = yaml.safe_load((WORKFLOWS / name).read_text())
    (job,) = workflow["jobs"].values()
    return job["steps"]


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


def errors(stdout):
    return [line for line in stdout.splitlines() if line.startswith("::error ")]


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
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(warnings(result.stdout), [])
        found = errors(result.stdout)
        self.assertEqual(len(found), len(expected), result.stdout)
        for line, path in zip(found, expected):
            self.assertTrue(line.startswith(f"::error title=Copied agent standards::{path} "), line)
            self.assertIn(CLEAN_URL, line)
            self.assertIn(f"- <code>{path}</code>", summary)
        self.assertIn(CLEAN_URL, summary)
        self.assertIn("The build fails until these paths are removed", summary)
        return result, summary

    def test_clean_project_passes(self):
        make(self.root, "src/index.js", ".claude/settings.json", ".agents/README.md")
        result, summary = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(warnings(result.stdout), [])
        self.assertEqual(errors(result.stdout), [])
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
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(errors(result.stdout), [])

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read any directory")
    def test_unreadable_skill_directory_does_not_fail(self):
        # Entries that cannot be listed are not findings.
        make(self.root, ".claude/skills/x/SKILL.md")
        skills = os.path.join(self.root, ".claude", "skills")
        os.chmod(skills, 0)
        self.addCleanup(os.chmod, skills, 0o755)
        result, _ = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(errors(result.stdout), [])

    def test_annotation_data_is_escaped(self):
        make(self.root, ".claude/skills/bad%0Aname\nnext/")
        result, _ = self.check()
        self.assertEqual(result.returncode, 1, result.stderr)
        found = errors(result.stdout)
        self.assertEqual(len(found), 1, result.stdout)
        self.assertIn("bad%250Aname%0Anext", found[0])

    def test_missing_project_checkout_is_a_visible_warning(self):
        result, summary = self.check({"COPIED_STANDARDS_ROOT": "caller-project"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(errors(result.stdout), [])
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
                self.assertEqual(errors(result.stdout), [])
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
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(errors(result.stdout), [])
        found = warnings(result.stdout)
        self.assertEqual(len(found), 1, result.stdout)
        self.assertIn("not checked", found[0])
        self.assertNotIn(".agent-standards.yml", summary)

    def test_successful_checkout_outcome_is_inspected(self):
        make(self.root, "caller-project/.agent-standards.yml")
        result, _ = self.check({"COPIED_STANDARDS_ROOT": "caller-project",
                                "CALLER_CHECKOUT_OUTCOME": "success"})
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(errors(result.stdout)), 1, result.stdout)
        self.assertIn(".agent-standards.yml", result.stdout)

    def test_summary_names_cannot_inject_markdown(self):
        name = "x` [spoof](https://evil.example) <a href=y>`"
        make(self.root, f".claude/skills/{name}/")
        result, summary = self.check()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(errors(result.stdout)), 1, result.stdout)
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

    def test_skill_name_cannot_hide_other_findings(self):
        # A name containing " .agents " must not be taken for a symlinked parent.
        make(self.root, ".claude/skills/x .agents y/", ".agents/skills/hidden/")
        result, summary = self.check()
        found = errors(result.stdout)
        self.assertEqual(len(found), 2, result.stdout)
        self.assertIn(".agents/skills/hidden", found[1])
        self.assertIn("- <code>.agents/skills/hidden</code>", summary)

    def test_bidi_and_control_names_are_still_reported(self):
        # Display disposition: such names are shown as-is (summary ASCII
        # punctuation and controls are entity-encoded), but each is reported
        # and none hides another finding.
        names = ["a\u202eexe.dm", "b\u2066c\u2069", "c\x1bd\te"]
        make(self.root, *[f".claude/skills/{n}/" for n in names], ".agents/skills/z/")
        result, summary = self.check()
        self.assertEqual(result.returncode, 1, result.stderr)
        found = errors(result.stdout)
        self.assertEqual(len(found), 4, result.stdout)
        self.assertIn(".agents/skills/z", found[-1])
        self.assertEqual(len([l for l in summary.splitlines() if l.startswith("- ")]), 4)
        self.assertIn("c&#27;d&#9;e", summary)

    def test_check_reads_nothing_from_upstream(self):
        body = script_body()
        for forbidden in ("git ", "curl", "wget", "TOKEN", "token", "http://"):
            self.assertNotIn(forbidden, body)
        self.assertEqual(body.count("https://"), 1)


class WorkflowIntegrationTest(unittest.TestCase):
    def steps(self, name):
        return workflow_steps(name)

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
                self.assertNotIn("continue-on-error", step)

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

    def test_embedded_step_fails_on_findings(self):
        for name, root in REUSABLE.items():
            with self.subTest(workflow=name), tempfile.TemporaryDirectory() as workspace:
                (step,) = [s for s in self.steps(name) if s.get("name") == STEP_NAME]
                make(os.path.join(workspace, root), ".agent-standards.yml",
                     ".claude/skills/x/SKILL.md")
                # Deployment checkouts beside the caller project are not inspected.
                make(workspace, "gitops/.agent-standards.yml", "ansible/.agents/core/x.md")
                result, summary = run_check(step["run"], workspace, step_env(step))
                self.assertEqual(result.returncode, 1, result.stderr)
                found = errors(result.stdout)
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
                self.assertEqual(errors(result.stdout), [])
                found = warnings(result.stdout)
                self.assertEqual(len(found), 1, result.stdout)
                self.assertIn("not checked", found[0])
                self.assertIn("Not checked", summary)
                self.assertNotIn("None found", summary)


def sparse_patterns(name):
    steps = workflow_steps(name)
    (checkout,) = [s for s in steps if s.get("id") == "caller-checkout"]
    with_ = checkout["with"]
    assert with_["sparse-checkout-cone-mode"] is False
    return with_["sparse-checkout"].splitlines()


def git(*args, cwd):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                   cwd=cwd, check=True, capture_output=True)


def sparse_clone(source, dest, patterns):
    """Non-cone sparse checkout as actions/checkout@v4 applies it."""
    git("clone", "--quiet", "--no-checkout", str(source), str(dest), cwd=source)
    git("config", "core.sparseCheckout", "true", cwd=dest)
    info = pathlib.Path(dest) / ".git" / "info"
    info.mkdir(exist_ok=True)
    with open(info / "sparse-checkout", "a") as f:
        f.write("\n" + "\n".join(patterns) + "\n")
    git("checkout", "--quiet", cwd=dest)


@unittest.skipUnless(shutil.which("git"), "git is required")
class SparseCheckoutIntegrationTest(unittest.TestCase):
    """Deployment workflows: real sparse checkout of a caller repo, then the embedded step."""

    def run_deployment(self, name, build):
        with tempfile.TemporaryDirectory() as tmp:
            source = pathlib.Path(tmp) / "source"
            source.mkdir()
            git("init", "--quiet", cwd=source)
            build(source)
            git("add", "-A", cwd=source)
            git("commit", "--quiet", "-m", "fixture", cwd=source)
            workspace = pathlib.Path(tmp) / "workspace"
            workspace.mkdir()
            root = REUSABLE[name]
            sparse_clone(source, workspace / root, sparse_patterns(name))
            (step,) = [s for s in workflow_steps(name)
                       if s.get("name") == STEP_NAME]
            result, summary = run_check(step["run"], workspace, step_env(step))
            found = errors(result.stdout)
            self.assertEqual(result.returncode, 1 if found else 0, result.stderr)
            self.assertEqual(warnings(result.stdout), [])
            checked_out = sorted(str(p.relative_to(workspace / root))
                                 for p in (workspace / root).rglob("*")
                                 if ".git" not in p.relative_to(workspace / root).parts)
            return found, summary, checked_out

    def deployments(self):
        return [name for name, root in REUSABLE.items() if root != "."]

    def test_symlinked_parents_are_checked_out_and_reported(self):
        def build(src):
            os.symlink("elsewhere", src / ".agents")
            os.symlink("/etc", src / ".claude")
            make(src, "src/index.js")
        for name in self.deployments():
            with self.subTest(workflow=name):
                found, summary, checked_out = self.run_deployment(name, build)
                self.assertEqual(len(found), 2, found)
                self.assertTrue(found[0].startswith(
                    "::error title=Copied agent standards::.agents "), found)
                self.assertTrue(found[1].startswith(
                    "::error title=Copied agent standards::.claude "), found)
                self.assertNotIn("None found", summary)
                self.assertEqual(checked_out, [".agents", ".claude"])

    def test_standards_are_reported_and_unrelated_files_are_not_checked_out(self):
        def build(src):
            make(src, ".agents/core/x.md", ".agent-standards.yml",
                 ".claude/skills/x .agents y/SKILL.md", ".agents/skills/hidden/SKILL.md",
                 ".agents/README.md", ".claude/settings.json", ".claude/other/x", "src/index.js")
        for name in self.deployments():
            with self.subTest(workflow=name):
                found, _, checked_out = self.run_deployment(name, build)
                self.assertEqual(len(found), 4, found)
                for line, path in zip(found, [".agents/core", ".agent-standards.yml",
                                              ".claude/skills/x .agents y",
                                              ".agents/skills/hidden"]):
                    self.assertTrue(line.startswith(
                        f"::error title=Copied agent standards::{path} "), line)
                for unrelated in (".agents/README.md", ".claude/settings.json",
                                  ".claude/other", "src"):
                    self.assertNotIn(unrelated, checked_out)

    def test_symlinks_below_parents_are_checked_out_and_reported(self):
        def build(src):
            (src / ".agents").mkdir()
            (src / ".claude").mkdir()
            os.symlink("/etc", src / ".agents" / "core")
            os.symlink("/etc", src / ".claude" / "skills")
            os.symlink("elsewhere", src / ".agents" / "skills")
        for name in self.deployments():
            with self.subTest(workflow=name):
                found, _, _ = self.run_deployment(name, build)
                self.assertEqual(len(found), 3, found)

    def test_clean_caller_is_reported_clean(self):
        for name in self.deployments():
            with self.subTest(workflow=name):
                found, summary, checked_out = self.run_deployment(
                    name, lambda src: make(src, "src/index.js", ".claude/settings.json"))
                self.assertEqual(found, [])
                self.assertIn("None found.", summary)
                self.assertEqual(checked_out, [])


if __name__ == "__main__":
    unittest.main()
