import sqlite3
import json

db_path = r"c:\Users\ignaz\antigravity\keen-franklin\.agents\context\sanctuary_context.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== PRAGMAS ===")
for pragma in ['journal_mode', 'busy_timeout', 'synchronous', 'foreign_keys', 'wal_autocheckpoint']:
    res = cursor.execute(f"PRAGMA {pragma};").fetchone()
    print(f"{pragma}: {res[0]}")

print("\n=== TABLES ===")
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
for t in tables:
    name = t["name"]
    print(f"\n--- Table: {name} ---")
    print(t["sql"])
    print("Columns (cid, name, type, notnull, dflt_value, pk):")
    for col in cursor.execute(f"PRAGMA table_info({name});").fetchall():
        print(tuple(col))
    cursor.execute(f"SELECT COUNT(*) FROM {name};")
    count = cursor.fetchone()[0]
    print(f"Row count: {count}")

print("\n=== ARTIFACTS ENTRIES ===")
cursor.execute("SELECT * FROM artifacts;")
artifacts = [dict(r) for r in cursor.fetchall()]
print(json.dumps(artifacts, indent=2))

print("\n=== EPOCHS ENTRIES ===")
cursor.execute("SELECT * FROM epochs;")
epochs = [dict(r) for r in cursor.fetchall()]
print(json.dumps(epochs, indent=2))

print("\n=== BENCHMARKS ENTRIES ===")
cursor.execute("SELECT * FROM benchmarks;")
benchmarks = [dict(r) for r in cursor.fetchall()]
print(json.dumps(benchmarks, indent=2))

print("\n=== RATE_LIMITS ENTRIES (Last 5) ===")
cursor.execute("SELECT * FROM rate_limits ORDER BY id DESC LIMIT 5;")
rate_limits = [dict(r) for r in cursor.fetchall()]
print(json.dumps(rate_limits, indent=2))

print("\n=== AGENT_MEMORIES ENTRIES (Last 5) ===")
cursor.execute("SELECT * FROM agent_memories ORDER BY id DESC LIMIT 5;")
memories = [dict(r) for r in cursor.fetchall()]
print(json.dumps(memories, indent=2))

conn.close()
