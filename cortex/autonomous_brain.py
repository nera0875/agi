"""
AGI Autonomous Brain - Système de polling et exécution autonome
Tourne en background, vérifie les worker_tasks, exécute les pending_instructions
Peut tourner indépendamment de Claude Code (survit aux interruptions de conversation)
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AGI.AutonomousBrain')

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'agi_user',
    'password': 'agi_password',
    'database': 'agi_db'
}

POLL_INTERVAL = 30  # seconds


class AutonomousBrain:
    """
    Cerveau autonome qui:
    - Poll worker_tasks toutes les 30s
    - Détecte les timeouts
    - Exécute les pending_instructions
    - Sauvegarde checkpoints
    - Peut reprendre après interruption
    """

    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.pool: asyncpg.Pool = None
        self.running = False
        self.session_id = None

    async def connect(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(**self.db_config)
        logger.info("✅ Connected to PostgreSQL")

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
        logger.info("❌ Database connections closed")

    async def get_or_create_session(self):
        """Get active session or create new one"""
        async with self.pool.acquire() as conn:
            # Try to get active session
            session = await conn.fetchrow("""
                SELECT * FROM active_context
                WHERE session_active = true
                ORDER BY updated_at DESC
                LIMIT 1
            """)

            if session:
                self.session_id = session['session_id']
                logger.info(f"📋 Restored session: {self.session_id}")
                return session

            # Create new session
            import uuid
            self.session_id = uuid.uuid4()

            import json
            await conn.execute("""
                INSERT INTO active_context (
                    session_id,
                    conversation_phase,
                    context_variables
                ) VALUES ($1, $2, $3::jsonb)
            """, self.session_id, 'autonomous_mode', json.dumps({
                'started_by': 'autonomous_brain',
                'started_at': datetime.now().isoformat()
            }))

            logger.info(f"🆕 Created new session: {self.session_id}")
            return None

    async def check_worker_tasks(self):
        """Check status of all worker tasks"""
        async with self.pool.acquire() as conn:
            # Get running tasks
            running_tasks = await conn.fetch("""
                SELECT *
                FROM worker_tasks
                WHERE status = 'running'
            """)

            for task in running_tasks:
                # Check for timeout
                timeout_threshold = task['created_at'] + timedelta(seconds=task['timeout_seconds'])

                if datetime.now() > timeout_threshold:
                    logger.warning(f"⏱️  Task {task['id']} timed out")

                    await conn.execute("""
                        UPDATE worker_tasks
                        SET status = 'failed',
                            error = 'Task exceeded timeout',
                            completed_at = now()
                        WHERE id = $1
                    """, task['id'])

            # Get recently completed tasks
            completed_tasks = await conn.fetch("""
                SELECT *
                FROM worker_tasks
                WHERE status = 'completed'
                AND completed_at > now() - interval '1 minute'
            """)

            for task in completed_tasks:
                logger.info(f"✅ Task {task['id']} completed: {task['task_type']}")

                # Check if there's a next_action in metadata
                metadata = task['metadata'] or {}
                if 'next_action' in metadata:
                    await self.queue_instruction(
                        metadata['next_action'],
                        priority=80,
                        context={'triggered_by': str(task['id'])}
                    )

            return len(running_tasks), len(completed_tasks)

    async def execute_pending_instructions(self):
        """Execute pending instructions from the queue"""
        async with self.pool.acquire() as conn:
            # Get pending instructions
            instructions = await conn.fetch("""
                SELECT *
                FROM pending_instructions
                WHERE status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT 5
            """)

            executed_count = 0

            for instruction in instructions:
                logger.info(f"🎯 Executing instruction: {instruction['instruction_text'][:100]}...")

                # Mark as executing
                await conn.execute("""
                    UPDATE pending_instructions
                    SET status = 'executing',
                        executed_at = now()
                    WHERE id = $1
                """, instruction['id'])

                try:
                    # Here you would actually execute the instruction
                    # For now, just log it
                    logger.info(f"   Type: {instruction['instruction_type']}")
                    logger.info(f"   Context: {instruction['execution_context']}")

                    # Mark as completed
                    await conn.execute("""
                        UPDATE pending_instructions
                        SET status = 'completed',
                            completed_at = now(),
                            result = $2
                        WHERE id = $1
                    """, instruction['id'], {
                        'status': 'success',
                        'executed_by': 'autonomous_brain'
                    })

                    executed_count += 1

                except Exception as e:
                    logger.error(f"❌ Error executing instruction: {e}")

                    await conn.execute("""
                        UPDATE pending_instructions
                        SET status = 'failed',
                            completed_at = now(),
                            result = $2
                        WHERE id = $1
                    """, instruction['id'], {
                        'status': 'error',
                        'error': str(e)
                    })

            return executed_count

    async def queue_instruction(self, instruction_text: str, priority: int = 50, context: dict = None):
        """Add instruction to pending queue"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO pending_instructions (
                    instruction_type,
                    instruction_text,
                    priority,
                    execution_context
                ) VALUES ($1, $2, $3, $4)
            """, 'system_task', instruction_text, priority, context or {})

            logger.info(f"📝 Queued instruction: {instruction_text[:50]}...")

    async def save_context(self, updates: dict):
        """Save current context state"""
        import json
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE active_context
                SET context_variables = context_variables || $1::jsonb,
                    updated_at = now()
                WHERE session_id = $2
            """, json.dumps(updates), self.session_id)

    async def get_dashboard(self):
        """Get system dashboard stats"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM system_dashboard")

    async def polling_loop(self):
        """Main autonomous polling loop"""
        self.running = True
        cycle_count = 0

        logger.info("🔄 Starting autonomous polling loop...")

        while self.running:
            try:
                cycle_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Polling Cycle #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")

                # 1. Check worker tasks
                running, completed = await self.check_worker_tasks()
                logger.info(f"📊 Worker tasks: {running} running, {completed} completed")

                # 2. Execute pending instructions
                executed = await self.execute_pending_instructions()
                if executed > 0:
                    logger.info(f"✅ Executed {executed} instructions")

                # 3. Get dashboard
                dashboard = await self.get_dashboard()
                logger.info(f"📈 Dashboard: {dict(dashboard)}")

                # 4. Save context
                await self.save_context({
                    'last_poll': datetime.now().isoformat(),
                    'cycle_count': cycle_count,
                    'running_tasks': running,
                    'completed_tasks': completed
                })

                # Wait for next cycle
                await asyncio.sleep(POLL_INTERVAL)

            except Exception as e:
                logger.error(f"❌ Error in polling loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Short wait before retry

    async def start(self):
        """Start the autonomous brain"""
        await self.connect()
        await self.get_or_create_session()

        logger.info("🧠 AGI Autonomous Brain started")
        logger.info(f"⏱️  Polling interval: {POLL_INTERVAL}s")

        try:
            await self.polling_loop()
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        finally:
            self.running = False
            await self.close()


async def main():
    brain = AutonomousBrain(DB_CONFIG)
    await brain.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down gracefully...")
        sys.exit(0)
