"""
Open-Source Web Systems Scaffold CLI
Generates production starter boilerplates and Docker Compose environments for the 4 core archetypes.
"""

import sys
import argparse
from pathlib import Path

BLUEPRINTS = {
    "laravel": {
        "name": "Laravel 11/12 + Filament v3 + FrankenPHP Octane",
        "description": "Full-stack Majestic Monolith with built-in admin, queue workers, Postgres 17, and Valkey.",
        "compose_file": "laravel-octane-postgres-valkey.yml",
        "doc": "08-production-scaffold-blueprints/laravel-filament-modern-monolith.md"
    },
    "nextjs": {
        "name": "Next.js 15+ + React 19 + Drizzle ORM",
        "description": "Full-stack TypeScript application with Server Components, Actions, Postgres 17, and Valkey.",
        "compose_file": "nextjs-drizzle-postgres-valkey.yml",
        "doc": "08-production-scaffold-blueprints/react-19-nextjs-drizzle-fullstack.md"
    },
    "fastapi": {
        "name": "FastAPI + Pydantic v2 + Async SQLAlchemy 2.0",
        "description": "High-throughput asynchronous Python microservice with Celery workers and Postgres 17.",
        "compose_file": "fastapi-celery-postgres-valkey.yml",
        "doc": "08-production-scaffold-blueprints/fastapi-pydantic-v2-sqlalchemy.md"
    },
    "go": {
        "name": "Go 1.23+ + Chi + sqlc Compile-Time SQL",
        "description": "Ultra-low-latency Go microservice with zero reflection, pgxpool, and Valkey.",
        "compose_file": "go-chi-postgres-valkey.yml",
        "doc": "08-production-scaffold-blueprints/go-chi-sqlc-microservice.md"
    },
    "supabase": {
        "name": "Supabase Self-Hosted Full-Stack (PostgreSQL 17, GoTrue, PostgREST, Realtime, Studio)",
        "description": "Complete open-source BaaS infrastructure with PostgreSQL 17, PostgREST, RLS auth, Realtime WebSockets, and Kong API Gateway.",
        "compose_file": "supabase-self-hosted-fullstack.yml",
        "doc": "05-open-source-baas-and-cms/01-supabase-and-pocketbase.md"
    }
}

def list_blueprints():
    print("\n=======================================================")
    print(" Available Open-Source Production Blueprints (2026)")
    print("=======================================================\n")
    for key, data in BLUEPRINTS.items():
        print(f"[{key.upper()}] {data['name']}")
        print(f"  Description: {data['description']}")
        print(f"  Docker Compose: 13-production-docker-compose-environments/{data['compose_file']}")
        print(f"  Specification: {data['doc']}\n")

def scaffold(blueprint_key: str, dest_dir: Path):
    if blueprint_key not in BLUEPRINTS:
        print(f"[ERROR] Unknown blueprint '{blueprint_key}'. Run with --list to see options.")
        return False

    bp = BLUEPRINTS[blueprint_key]
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy docker-compose
    compendium_root = Path(__file__).resolve().parent.parent
    src_compose = compendium_root / "13-production-docker-compose-environments" / bp["compose_file"]
    
    if src_compose.exists():
        target_compose = dest_dir / "docker-compose.yml"
        target_compose.write_text(src_compose.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[SUCCESS] Copied {bp['compose_file']} -> {target_compose}")

    # Generate .env.example
    env_content = (
        f"# Production Environment Configuration for {bp['name']}\n"
        f"APP_ENV=production\n"
        f"DB_PASSWORD=change_this_secure_production_password_123\n"
        f"REDIS_PASSWORD=change_this_valkey_password_123\n"
    )
    (dest_dir / ".env.example").write_text(env_content, encoding="utf-8")
    print(f"[SUCCESS] Created {dest_dir / '.env.example'}")
    
    print(f"\n[DONE] Scaffold initialized for '{bp['name']}' in {dest_dir.resolve()}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Open-Source Web Architecture Scaffolder")
    parser.add_argument("--list", action="store_true", help="List all available stack blueprints")
    parser.add_argument("--blueprint", type=str, choices=list(BLUEPRINTS.keys()), help="Target blueprint to scaffold")
    parser.add_argument("--output", type=str, default="./scaffolded_project", help="Destination output folder")

    args = parser.parse_args()

    if args.list or not args.blueprint:
        list_blueprints()
        if not args.blueprint:
            print("Tip: Use --blueprint <name> --output <dir> to scaffold an environment.")
            sys.exit(0)

    if args.blueprint:
        success = scaffold(args.blueprint, Path(args.output))
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
