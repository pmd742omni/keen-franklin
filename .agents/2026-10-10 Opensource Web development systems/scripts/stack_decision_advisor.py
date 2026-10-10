"""
Open-Source Web Architecture Decision Advisor (2026)
Interactive CLI that evaluates project constraints and provides quantitative
recommendations across Laravel, Next.js, FastAPI, Go, and Local-First / Supabase stacks.
"""

import sys
import argparse

STACK_PROFILES = {
    "laravel": {
        "title": "Laravel 11/12 + Filament v3 + FrankenPHP Octane",
        "archetypes": ["b2b_saas", "admin_portal", "solo_mvp", "enterprise_monolith"],
        "languages": ["php", "fullstack"],
        "max_traffic": "medium_high",
        "development_speed": 10,
        "runtime_efficiency": 8,
        "operational_simplicity": 9,
        "realtime_complexity": 7,
        "command": "python scripts/stack_scaffolder.py --blueprint laravel --output ./my-laravel-app",
        "rationales": [
            "Batteries-included majestic monolith with native queues, scheduling, authentication, and mail.",
            "Filament v3 offers instant auto-generated admin interfaces, tables, and forms with zero frontend JS build overhead.",
            "FrankenPHP Octane worker mode maintains state in RAM, yielding 1-3ms response times."
        ]
    },
    "nextjs": {
        "title": "Next.js 15+ + React 19 RSC + Drizzle ORM",
        "archetypes": ["public_web", "content_heavy", "b2b_saas", "ecommerce"],
        "languages": ["typescript", "javascript", "fullstack"],
        "max_traffic": "very_high",
        "development_speed": 9,
        "runtime_efficiency": 8,
        "operational_simplicity": 8,
        "realtime_complexity": 8,
        "command": "python scripts/stack_scaffolder.py --blueprint nextjs --output ./my-nextjs-app",
        "rationales": [
            "React 19 Server Components (RSC) stream HTML directly from backend data layers without client waterfalls.",
            "End-to-end TypeScript type safety across queries, Server Actions, and client components.",
            "Drizzle ORM provides zero-overhead SQL-like type safety without heavyweight ORM runtime caches."
        ]
    },
    "fastapi": {
        "title": "FastAPI + Pydantic v2 + Async SQLAlchemy 2.0",
        "archetypes": ["ai_ml_backend", "data_pipeline", "microservice", "b2b_saas"],
        "languages": ["python"],
        "max_traffic": "high",
        "development_speed": 8,
        "runtime_efficiency": 8,
        "operational_simplicity": 8,
        "realtime_complexity": 8,
        "command": "python scripts/stack_scaffolder.py --blueprint fastapi --output ./my-fastapi-app",
        "rationales": [
            "Native integration with Python AI/ML ecosystem (PyTorch, LangChain, Hugging Face, vLLM).",
            "Pydantic v2 core compiled in Rust for sub-millisecond JSON parsing and schema validation.",
            "Automatic OpenAPI 3.1 schema and interactive documentation generation."
        ]
    },
    "go": {
        "title": "Go 1.23+ + Chi Router + sqlc Compile-Time SQL",
        "archetypes": ["microservice", "high_throughput", "iot_gateway", "financial_ledger"],
        "languages": ["go"],
        "max_traffic": "extreme",
        "development_speed": 7,
        "runtime_efficiency": 10,
        "operational_simplicity": 10,
        "realtime_complexity": 9,
        "command": "python scripts/stack_scaffolder.py --blueprint go --output ./my-go-service",
        "rationales": [
            "Compiled static binary under 20MB with sub-millisecond cold starts and minimal RAM (<25MB idle).",
            "sqlc generates type-safe Go code from plain SQL queries at compile time with zero reflection overhead.",
            "Bounded goroutine worker pools handle tens of thousands of concurrent connections effortlessly."
        ]
    },
    "supabase": {
        "title": "Supabase Self-Hosted Full-Stack BaaS",
        "archetypes": ["solo_mvp", "mobile_backend", "realtime_collab", "rapid_prototype"],
        "languages": ["typescript", "any"],
        "max_traffic": "high",
        "development_speed": 10,
        "runtime_efficiency": 9,
        "operational_simplicity": 7,
        "realtime_complexity": 10,
        "command": "python scripts/stack_scaffolder.py --blueprint supabase --output ./my-supabase-baas",
        "rationales": [
            "Instant REST & GraphQL APIs directly mapped from PostgreSQL schema via PostgREST.",
            "Row Level Security (RLS) policies enforce security directly in the PostgreSQL kernel.",
            "Built-in Realtime WebSockets streaming Postgres WAL changes with low latency."
        ]
    }
}

def score_stack(profile, use_case, language, priority):
    score = 0
    # Use-case match
    if use_case in profile["archetypes"]:
        score += 40
    # Language preference match
    if language in profile["languages"] or "any" in profile["languages"]:
        score += 30
    elif "fullstack" in profile["languages"] and language in ["typescript", "javascript"]:
        score += 25
    
    # Priority adjustments
    if priority == "speed":
        score += profile["development_speed"] * 3
    elif priority == "performance":
        score += profile["runtime_efficiency"] * 3
    elif priority == "simplicity":
        score += profile["operational_simplicity"] * 3
    elif priority == "realtime":
        score += profile["realtime_complexity"] * 3

    return score

def advise(use_case: str, language: str, priority: str):
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("\n=======================================================")
    print(" 2026 Open-Source Web Architecture Recommendation")
    print("=======================================================\n")
    print(f"Inputs -> Archetype: {use_case.upper()} | Language: {language.upper()} | Priority: {priority.upper()}\n")

    ranked = []
    for key, profile in STACK_PROFILES.items():
        points = score_stack(profile, use_case, language, priority)
        ranked.append((points, key, profile))

    ranked.sort(key=lambda x: x[0], reverse=True)

    winner_score, winner_key, winner = ranked[0]

    print(f"[TOP RECOMMENDATION] {winner['title']}")
    print(f"   Match Score: {winner_score}/100")
    print("\n[Architectural Rationales]")
    for r in winner["rationales"]:
        print(f"   - {r}")
    
    print(f"\n[Scaffolding Command]\n   {winner['command']}\n")

    print("-------------------------------------------------------")
    print("[Runner-Up Alternatives]")
    for score, key, prof in ranked[1:3]:
        print(f"   - {prof['title']} (Score: {score}/100)")
    print("=======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Open-Source Web Architecture Decision Advisor")
    parser.add_argument("--use-case", choices=["b2b_saas", "public_web", "microservice", "ai_ml_backend", "solo_mvp", "realtime_collab"], default="b2b_saas", help="Application Archetype")
    parser.add_argument("--language", choices=["typescript", "php", "python", "go"], default="typescript", help="Team Primary Language")
    parser.add_argument("--priority", choices=["speed", "performance", "simplicity", "realtime"], default="speed", help="Key Architectural Priority")

    args = parser.parse_args()
    advise(args.use_case, args.language, args.priority)

if __name__ == "__main__":
    main()
