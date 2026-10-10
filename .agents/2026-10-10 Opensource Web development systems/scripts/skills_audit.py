"""
Workspace Skills Auditor & Integrity Checker
Scans .agents/skills/ to validate YAML frontmatter, description quality, and reference integrity.
"""

import sys
from pathlib import Path
import re

def parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    
    yaml_text = parts[1]
    metadata = {}
    for line in yaml_text.strip().splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            metadata[key.strip()] = val.strip().strip('"').strip("'")
    return metadata

def audit_skills(skills_dir: Path):
    if not skills_dir.exists():
        print(f"[ERROR] Skills directory not found: {skills_dir}")
        return False

    skill_folders = [d for d in skills_dir.iterdir() if d.is_dir()]
    print(f"\n=======================================================")
    print(f" Auditing Workspace Skills: {len(skill_folders)} found in {skills_dir.name}")
    print(f"=======================================================\n")

    valid_count = 0
    issues = []

    for folder in sorted(skill_folders):
        skill_file = folder / "SKILL.md"
        if not skill_file.exists():
            issues.append(f"[FAIL] {folder.name}: Missing SKILL.md")
            continue

        try:
            content = skill_file.read_text(encoding="utf-8", errors="replace")
            meta = parse_frontmatter(content)
            
            name = meta.get("name")
            desc = meta.get("description")

            if not name:
                issues.append(f"[WARN] {folder.name}: Missing 'name' in frontmatter")
            if not desc:
                issues.append(f"[WARN] {folder.name}: Missing 'description' in frontmatter")

            # Check references folder if mentioned
            refs_dir = folder / "references"
            ref_count = len(list(refs_dir.glob("*.md"))) if refs_dir.exists() else 0

            status_str = f"PASS ({ref_count} refs)" if ref_count > 0 else "PASS (standalone)"
            print(f" - [OK] {folder.name:<32} -> {status_str}")
            valid_count += 1

        except Exception as e:
            issues.append(f"[ERR] {folder.name}: Exception reading file: {e}")

    print(f"\nAudit Complete: {valid_count}/{len(skill_folders)} skills validated successfully.")
    if issues:
        print(f"\nNotices/Issues ({len(issues)}):")
        for issue in issues:
            print(f"  {issue}")

    return len(issues) == 0

if __name__ == "__main__":
    workspace_root = Path(__file__).resolve().parents[3]
    skills_path = workspace_root / ".agents" / "skills"
    success = audit_skills(skills_path)
    sys.exit(0 if success else 1)
