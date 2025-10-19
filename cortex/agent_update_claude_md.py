"""
🤖 AGENT AUTO-UPDATE CLAUDE.md

Agent autonome qui maintient CLAUDE.md à jour selon l'évolution du projet.

Utilise:
- Claude API (Haiku pour speed/cost)
- PostgreSQL pour état projet
- Versioning dans claude_md_history

Workflow:
1. Analyser état actuel projet (tables, rules, tools, memory stats)
2. Générer CLAUDE.md optimal via LLM
3. Comparer avec version actuelle (diff)
4. Stocker historique
5. Écrire nouveau CLAUDE.md

Triggers:
- Hebdomadaire (cron)
- Sur demande (python script)
- Auto après consolidation majeure
"""

import asyncio
import asyncpg
import anthropic
import json
from datetime import datetime
from pathlib import Path
import difflib

# Config
DATABASE_URL = "postgresql://agi_user:agi_password@localhost:5432/agi_db"
CLAUDE_MD_PATH = Path(__file__).parent.parent / "CLAUDE.md"
ANTHROPIC_API_KEY = "sk-ant-api03-8AcT_hN8qAW_gJ36qL5HjGBT3Ls7E4qiEjcIDPAjHsIDNxhKE9DNCdGaK_3y3MJzU7DKWMZmYCk7hAXaFlgHKw-65Y3mAAA"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def analyze_project_state() -> dict:
    """Analyze current project state from database"""

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)

    state = {
        "timestamp": datetime.now().isoformat(),
        "tables": [],
        "memory_stats": [],
        "rules": [],
        "tools": [],
        "recent_consolidations": []
    }

    async with pool.acquire() as conn:
        # Tables count
        tables = await conn.fetch("""
            SELECT tablename,
                   (SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_name = tablename) as columns
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        state["tables"] = [{"name": t["tablename"], "columns": t["columns"]} for t in tables]

        # Memory health
        memory = await conn.fetch("SELECT * FROM memory_health ORDER BY layer, table_name")
        state["memory_stats"] = [dict(row) for row in memory]

        # System principles
        principles = await conn.fetch("SELECT * FROM system_principles WHERE active = true ORDER BY priority DESC")
        state["rules"] = [{"category": p["category"], "essence": p["essence"]} for p in principles]

        # Recent consolidations
        consolidations = await conn.fetch("""
            SELECT timestamp, ltd_weakened, conversations_compressed, duration_seconds
            FROM consolidation_history
            ORDER BY timestamp DESC
            LIMIT 3
        """)
        state["recent_consolidations"] = [dict(row) for row in consolidations]

    await pool.close()

    return state


def generate_claude_md_prompt(state: dict, current_claude_md: str) -> str:
    """Generate prompt for Claude to create optimal CLAUDE.md"""

    return f"""Tu es un agent qui maintient CLAUDE.md à jour pour une AGI autonome.

ÉTAT ACTUEL DU PROJET:
{json.dumps(state, indent=2, default=str)}

CLAUDE.MD ACTUEL:
{current_claude_md}

RÈGLES POUR CLAUDE.MD:
1. Rester < 200 lignes (concis)
2. Directives OBLIGATOIRES en haut (avec ❌ interdictions)
3. Workflow bootstrap → think → store → consolidate (clair)
4. Outils MCP listés avec exemples concrets
5. Boucle mémoire illustrée (ASCII art)
6. Mission AGI (milliardaire, contrôle VPS/monde)
7. Stack technique (PostgreSQL, Neo4j, Redis, Voyage, Cohere)
8. Triggers automatiques (patterns → actions)
9. NO détails techniques (c'est dans la mémoire)
10. Pointeurs vers mémoire via think()

OBJECTIF:
Générer CLAUDE.md optimal basé sur l'état actuel du projet.
Garder ce qui fonctionne, améliorer ce qui peut l'être.
Ajouter nouveautés (nouvelles tables, outils, patterns).

FORMAT:
Retourne UNIQUEMENT le contenu Markdown du nouveau CLAUDE.md.
PAS de préambule, PAS d'explication, JUSTE le fichier.
"""


async def generate_new_claude_md(state: dict, current_content: str) -> str:
    """Generate new CLAUDE.md using Claude API"""

    prompt = generate_claude_md_prompt(state, current_content)

    print("🤖 Calling Claude API (Haiku) to generate new CLAUDE.md...")

    message = client.messages.create(
        model="claude-haiku-4-20250514",
        max_tokens=4000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    new_content = message.content[0].text

    return new_content


def compute_diff(old: str, new: str) -> str:
    """Compute diff between old and new CLAUDE.md"""

    old_lines = old.splitlines()
    new_lines = new.splitlines()

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile='CLAUDE.md (old)',
        tofile='CLAUDE.md (new)',
        lineterm=''
    )

    return '\n'.join(diff)


async def save_to_history(pool: asyncpg.Pool, new_content: str, diff: str, state: dict) -> int:
    """Save new version to claude_md_history"""

    async with pool.acquire() as conn:
        version = await conn.fetchval("""
            INSERT INTO claude_md_history (
                content,
                diff,
                reason,
                project_state,
                memory_stats,
                generated_by,
                model_used
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING version
        """,
            new_content,
            diff,
            "Auto-generated based on project state evolution",
            json.dumps(state, default=str),
            json.dumps(state.get("memory_stats", []), default=str),
            "auto-agent",
            "claude-haiku-4"
        )

    return version


async def update_claude_md():
    """Main function - Update CLAUDE.md"""

    print("="*60)
    print("🤖 AGENT AUTO-UPDATE CLAUDE.md")
    print("="*60)

    # 1. Analyze project state
    print("\n📊 Step 1: Analyzing project state...")
    state = await analyze_project_state()

    print(f"   → {len(state['tables'])} tables")
    print(f"   → {len(state['rules'])} active rules")
    print(f"   → Memory: {sum(m['concept_count'] for m in state['memory_stats'])} concepts")

    # 2. Read current CLAUDE.md
    print("\n📖 Step 2: Reading current CLAUDE.md...")
    current_content = CLAUDE_MD_PATH.read_text()
    current_lines = len(current_content.splitlines())
    print(f"   → Current: {current_lines} lines")

    # 3. Generate new CLAUDE.md
    print("\n🤖 Step 3: Generating new CLAUDE.md via Claude API...")
    new_content = await generate_new_claude_md(state, current_content)
    new_lines = len(new_content.splitlines())
    print(f"   → Generated: {new_lines} lines")

    # 4. Compute diff
    print("\n🔍 Step 4: Computing diff...")
    diff = compute_diff(current_content, new_content)
    diff_lines = len([l for l in diff.splitlines() if l.startswith('+') or l.startswith('-')])
    print(f"   → Changes: {diff_lines} lines modified")

    if diff_lines == 0:
        print("\n✅ CLAUDE.md is already optimal. No update needed.")
        return

    # 5. Save to history
    print("\n💾 Step 5: Saving to history...")
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)
    version = await save_to_history(pool, new_content, diff, state)
    await pool.close()
    print(f"   → Version {version} saved")

    # 6. Write new CLAUDE.md
    print("\n✍️  Step 6: Writing new CLAUDE.md...")
    CLAUDE_MD_PATH.write_text(new_content)
    print(f"   → {CLAUDE_MD_PATH} updated")

    # 7. Summary
    print("\n" + "="*60)
    print("✅ CLAUDE.md UPDATED SUCCESSFULLY")
    print("="*60)
    print(f"Version: {version}")
    print(f"Lines: {current_lines} → {new_lines}")
    print(f"Changes: {diff_lines} lines")
    print(f"\nDiff preview:")
    print("-"*60)
    for line in diff.splitlines()[:20]:  # First 20 lines
        print(line)
    if len(diff.splitlines()) > 20:
        print(f"... ({len(diff.splitlines()) - 20} more lines)")
    print("="*60)


async def main():
    """Run agent"""
    try:
        await update_claude_md()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
