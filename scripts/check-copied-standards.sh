#!/usr/bin/env bash
# Warning-only check for copied agent standards in the caller project.
# Every reusable workflow embeds this exact body (after this header) in its
# "Check for copied agent standards" step; tests/test_copied_standards.py
# keeps the copies identical. Always exits 0.
root="${COPIED_STANDARDS_ROOT:-.}"
clean_url="https://github.com/ute-workspace/agent-standards/blob/main/scripts/clean-project.py"
summary="${GITHUB_STEP_SUMMARY:-/dev/null}"
escape() { local s="${1//%/%25}"; s="${s//$'\r'/%0D}"; printf '%s' "${s//$'\n'/%0A}"; }
if [ ! -d "$root" ]; then
  echo "::warning title=Copied agent standards::Project checkout '$(escape "$root")' not found; copied agent standards were not checked."
  printf '## Copied agent standards\n\nNot checked: project checkout `%s` not found.\n' "$root" >> "$summary"
  exit 0
fi
found=()
for path in .agents/core .agent-standards.yml; do
  if [ -e "$root/$path" ] || [ -L "$root/$path" ]; then found+=("$path"); fi
done
for dir in .claude/skills .agents/skills; do
  [ -d "$root/$dir" ] || continue
  while IFS= read -r -d '' entry; do
    found+=("$dir/${entry##*/}")
  done < <(find "$root/$dir" -mindepth 1 -maxdepth 1 -print0 | sort -z)
done
if [ "${#found[@]}" -eq 0 ]; then
  echo "No copied agent standards found."
  printf '## Copied agent standards\n\nNone found.\n' >> "$summary"
  exit 0
fi
{
  printf '## Copied agent standards\n\n'
  printf 'Warning only; the build is not failed. Remove these paths with [scripts/clean-project.py](%s):\n\n' "$clean_url"
} >> "$summary"
for path in "${found[@]}"; do
  echo "::warning title=Copied agent standards::$(escape "$path") is a copy of agent standards; remove it with $clean_url"
  printf -- '- `%s`\n' "$path" >> "$summary"
done
