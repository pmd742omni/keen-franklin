"""
Unified Workspace & Compendium Diagnostic Suite (2026)
Runs comprehensive end-to-end checks across:
1. Skills Suite compliance (YAML frontmatter & references)
2. Blueprint registry & Scaffolder integrity
3. Architecture Decision Advisor scoring
4. Compendium structural completeness (16 domains, file counts, zero broken markdown links)
"""

import sys
import os
import re
from pathlib import Path

# Configure UTF-8 stdout for Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

COMPENDIUM_DIR = Path(__file__).resolve().parent.parent
AGENTS_DIR = COMPENDIUM_DIR.parent
SKILLS_DIR = AGENTS_DIR / "skills"

def check_skills():
    print("[1/4] Running Skills Suite Audit...")
    from skills_audit import audit_skills
    success = audit_skills(SKILLS_DIR)
    if success:
        print("      PASS: Workspace skills suite fully compliant with zero issues.")
        return True
    else:
        print("      FAIL: Skills suite encountered validation issues.")
        return False

def check_scaffolder():
    print("\n[2/4] Testing Stack Scaffolder Registry...")
    from stack_scaffolder import BLUEPRINTS
    required_blueprints = ["laravel", "nextjs", "fastapi", "go", "supabase"]
    missing = [b for b in required_blueprints if b not in BLUEPRINTS]
    
    if missing:
        print(f"      FAIL: Missing blueprints: {missing}")
        return False
    
    compose_dir = COMPENDIUM_DIR / "13-production-docker-compose-environments"
    for key, data in BLUEPRINTS.items():
        compose_file = compose_dir / data["compose_file"]
        if not compose_file.exists():
            print(f"      FAIL: Missing compose file {compose_file}")
            return False
            
    print(f"      PASS: All {len(BLUEPRINTS)} production blueprints verified with Compose YAML files.")
    return True

def check_advisor():
    print("\n[3/4] Testing Stack Decision Advisor Scoring Engine...")
    from stack_decision_advisor import STACK_PROFILES, score_stack
    
    test_cases = [
        ("b2b_saas", "php", "speed", "laravel"),
        ("microservice", "go", "performance", "go"),
        ("ai_ml_backend", "python", "speed", "fastapi"),
        ("public_web", "typescript", "speed", "nextjs"),
    ]
    
    all_passed = True
    for use_case, lang, prio, expected in test_cases:
        ranked = []
        for key, profile in STACK_PROFILES.items():
            s = score_stack(profile, use_case, lang, prio)
            ranked.append((s, key))
        ranked.sort(key=lambda x: x[0], reverse=True)
        top_key = ranked[0][1]
        if top_key != expected:
            print(f"      FAIL: Expected {expected} for {use_case}/{lang}/{prio}, got {top_key}")
            all_passed = False
    
    if all_passed:
        print("      PASS: Decision algorithm correctly matches all test archetype profiles.")
    return all_passed

def check_compendium_integrity():
    print("\n[4/4] Verifying Compendium Structural Completeness...")
    domain_dirs = [d for d in COMPENDIUM_DIR.iterdir() if d.is_dir() and re.match(r"^\d{2}-", d.name)]
    root_domain_files = [f for f in COMPENDIUM_DIR.iterdir() if f.is_file() and re.match(r"^\d{2}-", f.name)]
    
    total_domains = len(domain_dirs) + len(root_domain_files)
    print(f"      Discovered {total_domains} architectural domains ({len(domain_dirs)} module directories + {len(root_domain_files)} foundational matrices).")
    
    total_md_files = len(root_domain_files)
    broken_links = 0
    
    for domain in domain_dirs:
        md_files = list(domain.glob("*.md"))
        total_md_files += len(md_files)
        
        # Check markdown relative links
        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8")
            links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
            for text, link in links:
                if link.startswith("http") or link.startswith("file:"):
                    continue
                target = (md_file.parent / link).resolve()
                if not target.exists():
                    print(f"      WARNING: Broken link in {md_file.name}: {link}")
                    broken_links += 1

    print(f"      Total Markdown Guides: {total_md_files}")
    print(f"      Broken Relative Links: {broken_links}")
    
    if total_domains >= 17 and broken_links == 0:
        print("      PASS: Compendium integrity verified with zero broken internal links across all 17 domains.")
        return True
    return False

def main():
    print("=======================================================")
    print(" 2026 Workspace & Compendium Diagnostic Suite")
    print("=======================================================\n")
    
    results = [
        check_skills(),
        check_scaffolder(),
        check_advisor(),
        check_compendium_integrity()
    ]
    
    print("\n=======================================================")
    if all(results):
        print(" [ALL PASS] All 4 diagnostic suites completed with 100% compliance!")
        print("=======================================================\n")
        sys.exit(0)
    else:
        print(" [FAIL] Diagnostic suite encountered errors.")
        print("=======================================================\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
