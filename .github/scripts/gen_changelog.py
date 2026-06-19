"""Generate grouped changelog from git log since last tag."""

import re
import subprocess
import sys

prev = subprocess.run(
    ["git", "describe", "--tags", "--abbrev=0", "HEAD^"],
    capture_output=True, text=True,
).stdout.strip()

range_spec = prev + "..HEAD" if prev else "HEAD"

r = subprocess.run(
    ["git", "log", "--format=%s", range_spec],
    capture_output=True, text=True,
)
commits = [l.strip() for l in r.stdout.split("\n") if l.strip()]

sections = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "test": "Tests",
    "ci": "CI / Chore",
    "chore": "CI / Chore",
}
order = ["feat", "fix", "refactor", "docs", "test", "ci", "chore"]
grouped: dict[str, list[str]] = {}

for line in commits:
    matched = False
    for prefix in order:
        if line.startswith(prefix + "(") or line.startswith(prefix + ":"):
            grouped.setdefault(prefix, []).append(line)
            matched = True
            break
    if not matched:
        grouped.setdefault("other", []).append(line)

lines = ["## What's Changed\n"]
for prefix in order:
    if prefix not in grouped:
        continue
    lines.append(f"### {sections[prefix]}")
    for msg in grouped[prefix]:
        clean = re.sub(r"^[^(:]+(\([^)]+\))?:\s*", "", msg).capitalize()
        lines.append(f"- {clean}")
    lines.append("")

if "other" in grouped:
    lines.append("### Other")
    for msg in grouped["other"]:
        lines.append(f"- {msg}")
    lines.append("")

sys.stdout.write("\n".join(lines).strip())
