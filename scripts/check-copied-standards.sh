#!/usr/bin/env bash
# Check for copied agent standards in the caller project.
# Every reusable workflow embeds this exact body (after this header) in its
# "Check for copied agent standards" step; tests/test_copied_standards.py
# keeps the copies identical. Exits 1 with an error annotation per finding;
# exits 0 when nothing is found or the project checkout cannot be checked.
root="${COPIED_STANDARDS_ROOT:-.}"
outcome="${CALLER_CHECKOUT_OUTCOME-success}"
clean_url="https://github.com/ute-workspace/agent-standards/blob/main/scripts/clean-project.py"
summary="${GITHUB_STEP_SUMMARY:-/dev/null}"
escape() { local s="${1//%/%25}"; s="${s//$'\r'/%0D}"; printf '%s' "${s//$'\n'/%0A}"; }
# Summary text: ASCII other than [A-Za-z0-9._/-] becomes an HTML entity, so names cannot form Markdown or HTML.
md() {
  local LC_ALL=C s="$1" out="" c n i
  for ((i = 0; i < ${#s}; i++)); do
    c="${s:i:1}"
    case "$c" in
      [A-Za-z0-9._/-]) out+="$c" ;;
      *) printf -v n '%d' "'$c"; if ((n < 0 || n > 127)); then out+="$c"; else out+="&#$n;"; fi ;;
    esac
  done
  printf '%s' "$out"
}
not_checked() {
  echo "::warning title=Copied agent standards::Project checkout '$(escape "$root")' $(escape "$1"); copied agent standards were not checked."
  printf '## Copied agent standards\n\nNot checked: project checkout <code>%s</code> %s.\n' "$(md "$root")" "$(md "$1")" >> "$summary"
  exit 0
}
[ "$outcome" = success ] || not_checked "failed (checkout outcome: ${outcome:-unknown})"
[ -d "$root" ] && [ ! -L "$root" ] || not_checked "not found"
found=()
linked=" "
for parent in .agents .claude; do
  # A symlinked parent is reported itself; its target is not listed.
  if [ -L "$root/$parent" ]; then found+=("$parent"); linked+="$parent "; fi
done
for path in .agents/core .agent-standards.yml .claude/skills .agents/skills; do
  # Only fixed parent names are matched, never names found in the project.
  case "$linked" in *" ${path%%/*} "*) continue ;; esac
  if [ -L "$root/$path" ] || { [ -e "$root/$path" ] && [ ! -d "$root/$path" ]; }; then
    found+=("$path")
  elif [ -d "$root/$path" ]; then
    case "$path" in
      */skills)
        while IFS= read -r -d '' entry; do
          found+=("$path/${entry##*/}")
        done < <(find "$root/$path" -mindepth 1 -maxdepth 1 -print0 | sort -z) ;;
      *) found+=("$path") ;;
    esac
  fi
done
if [ "${#found[@]}" -eq 0 ]; then
  echo "No copied agent standards found."
  printf '## Copied agent standards\n\nNone found.\n' >> "$summary"
  exit 0
fi
{
  printf '## Copied agent standards\n\n'
  printf 'The build fails until these paths are removed with [scripts/clean-project.py](%s):\n\n' "$clean_url"
} >> "$summary"
for path in "${found[@]}"; do
  echo "::error title=Copied agent standards::$(escape "$path") is a copy of agent standards; remove it with $clean_url"
  printf -- '- <code>%s</code>\n' "$(md "$path")" >> "$summary"
done
exit 1
