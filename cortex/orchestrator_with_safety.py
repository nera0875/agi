"""
Example: Integration of GitSafetyWrapper into Orchestrator
Demonstrates how to use git_safety_integration with agent orchestration
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from cortex.git_safety_integration import SafeOrchestrator, run_with_safety

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrchestratorWithSafety:
    """
    Enhanced orchestrator that integrates git safety for all agent tasks
    Provides safe execution of agent workloads with automatic checkpointing
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.safe_orch = SafeOrchestrator(project_root)
        self.project_root = project_root or Path(__file__).parent.parent

    async def execute_feature_workflow(self, feature_name: str,
                                     backend_tasks: List[Dict[str, str]],
                                     frontend_tasks: List[Dict[str, str]],
                                     test_tasks: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Execute complete feature workflow with safety:
        1. Backend implementation (code agent)
        2. Frontend implementation (frontend agent)
        3. Testing (debug agent)

        Args:
            feature_name: Name of feature being implemented
            backend_tasks: List of backend tasks {prompt, file_path}
            frontend_tasks: List of frontend tasks {prompt, file_path}
            test_tasks: List of test tasks {prompt}

        Returns:
            Workflow results with status and history
        """
        logger.info(f"=" * 80)
        logger.info(f"FEATURE WORKFLOW: {feature_name}")
        logger.info(f"=" * 80)

        results = {
            "feature": feature_name,
            "started_at": datetime.now().isoformat(),
            "phases": {
                "backend": [],
                "frontend": [],
                "tests": []
            },
            "overall_success": True,
            "errors": []
        }

        # PHASE 1: Backend Implementation
        if backend_tasks:
            logger.info(f"\n[Phase 1] Backend Implementation ({len(backend_tasks)} tasks)")
            logger.info("-" * 80)

            for i, task in enumerate(backend_tasks, 1):
                prompt = task.get("prompt", "")
                file_path = task.get("file_path", "")
                is_critical = self.safe_orch.safety.is_critical_file(file_path)

                logger.info(f"  Task {i}/{len(backend_tasks)}: {prompt[:60]}...")

                result = self.safe_orch.run_agent_safe(
                    agent_type="code",
                    prompt=prompt,
                    critical=is_critical,
                    file_path=file_path
                )

                results["phases"]["backend"].append(result)

                if not result["success"]:
                    results["overall_success"] = False
                    results["errors"].append(f"Backend task {i} failed: {result['error']}")
                    logger.warning(f"  ✗ Task {i} failed: {result['error']}")
                    break  # Stop on first error
                else:
                    logger.info(f"  ✓ Task {i} completed ({result['duration']:.2f}s)")

        # PHASE 2: Frontend Implementation
        if frontend_tasks and results["overall_success"]:
            logger.info(f"\n[Phase 2] Frontend Implementation ({len(frontend_tasks)} tasks)")
            logger.info("-" * 80)

            for i, task in enumerate(frontend_tasks, 1):
                prompt = task.get("prompt", "")
                file_path = task.get("file_path", "")

                logger.info(f"  Task {i}/{len(frontend_tasks)}: {prompt[:60]}...")

                result = self.safe_orch.run_agent_safe(
                    agent_type="frontend",
                    prompt=prompt,
                    critical=False,
                    file_path=file_path
                )

                results["phases"]["frontend"].append(result)

                if not result["success"]:
                    results["overall_success"] = False
                    results["errors"].append(f"Frontend task {i} failed: {result['error']}")
                    logger.warning(f"  ✗ Task {i} failed: {result['error']}")
                    break
                else:
                    logger.info(f"  ✓ Task {i} completed ({result['duration']:.2f}s)")

        # PHASE 3: Testing
        if test_tasks and results["overall_success"]:
            logger.info(f"\n[Phase 3] Testing ({len(test_tasks)} tasks)")
            logger.info("-" * 80)

            for i, task in enumerate(test_tasks, 1):
                prompt = task.get("prompt", "")

                logger.info(f"  Task {i}/{len(test_tasks)}: {prompt[:60]}...")

                result = self.safe_orch.run_agent_safe(
                    agent_type="debug",
                    prompt=prompt,
                    critical=False
                )

                results["phases"]["tests"].append(result)

                if not result["success"]:
                    results["overall_success"] = False
                    results["errors"].append(f"Test task {i} failed: {result['error']}")
                    logger.warning(f"  ✗ Task {i} failed: {result['error']}")
                else:
                    logger.info(f"  ✓ Task {i} completed ({result['duration']:.2f}s)")

        # Summary
        results["completed_at"] = datetime.now().isoformat()
        results["total_tasks"] = len(backend_tasks) + len(frontend_tasks) + len(test_tasks)
        results["successful_tasks"] = sum(
            len([t for t in tasks if t.get("success")])
            for tasks in results["phases"].values()
        )

        logger.info(f"\n" + "=" * 80)
        logger.info(f"WORKFLOW COMPLETE: {feature_name}")
        logger.info(f"Status: {'✅ SUCCESS' if results['overall_success'] else '❌ FAILED'}")
        logger.info(f"Tasks: {results['successful_tasks']}/{results['total_tasks']} successful")
        if results["errors"]:
            logger.error(f"Errors: {len(results['errors'])}")
            for err in results["errors"]:
                logger.error(f"  - {err}")
        logger.info(f"=" * 80)

        return results

    async def execute_refactoring(self, target_file: str,
                                refactor_prompt: str,
                                test_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Safely refactor a file with automatic backup and testing

        Args:
            target_file: File to refactor
            refactor_prompt: Refactoring instructions
            test_prompt: Optional prompt for testing refactored code

        Returns:
            Refactoring results
        """
        logger.info(f"\n" + "=" * 80)
        logger.info(f"REFACTORING: {target_file}")
        logger.info(f"=" * 80)

        results = {
            "file": target_file,
            "started_at": datetime.now().isoformat(),
            "phases": {}
        }

        # Check if file is critical
        is_critical = self.safe_orch.safety.is_critical_file(target_file)
        logger.info(f"Critical file: {'Yes' if is_critical else 'No'}")

        # Phase 1: Refactoring
        logger.info(f"\n[Phase 1] Refactoring")
        refactor_result = self.safe_orch.run_agent_safe(
            agent_type="code",
            prompt=refactor_prompt,
            critical=is_critical,
            file_path=target_file
        )
        results["phases"]["refactor"] = refactor_result

        if not refactor_result["success"]:
            logger.error(f"Refactoring failed: {refactor_result['error']}")
            results["overall_success"] = False
            return results

        logger.info(f"✓ Refactoring completed ({refactor_result['duration']:.2f}s)")

        # Phase 2: Testing (optional)
        if test_prompt:
            logger.info(f"\n[Phase 2] Testing")
            test_result = self.safe_orch.run_agent_safe(
                agent_type="debug",
                prompt=test_prompt,
                critical=False
            )
            results["phases"]["test"] = test_result

            if not test_result["success"]:
                logger.warning(f"Tests failed: {test_result['error']}")
                results["overall_success"] = False
            else:
                logger.info(f"✓ Tests passed ({test_result['duration']:.2f}s)")
                results["overall_success"] = True
        else:
            results["overall_success"] = True

        results["completed_at"] = datetime.now().isoformat()

        logger.info(f"\n" + "=" * 80)
        logger.info(f"REFACTORING COMPLETE")
        logger.info(f"Status: {'✅ SUCCESS' if results['overall_success'] else '❌ FAILED'}")
        logger.info(f"=" * 80)

        return results

    def export_workflow_report(self, output_file: Optional[Path] = None) -> str:
        """
        Export complete workflow history and analysis

        Args:
            output_file: Optional path to write report to

        Returns:
            JSON report string
        """
        history_json = self.safe_orch.export_history(output_file)
        return history_json


# Example usage
async def main():
    """Demonstrate orchestrator with safety integration"""

    orch = OrchestratorWithSafety()

    # Example 1: Simple feature workflow
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Feature Workflow")
    print("=" * 80)

    result = await orch.execute_feature_workflow(
        feature_name="Notification System",
        backend_tasks=[
            {
                "prompt": "Create GraphQL subscription for notifications",
                "file_path": "backend/api/schema.py"
            },
            {
                "prompt": "Add notification service implementation",
                "file_path": "backend/services/notification_service.py"
            }
        ],
        frontend_tasks=[
            {
                "prompt": "Create useNotification hook for Apollo subscriptions",
                "file_path": "frontend/src/hooks/use-notification.ts"
            },
            {
                "prompt": "Create NotificationCenter component",
                "file_path": "frontend/src/components/notification-center.tsx"
            }
        ],
        test_tasks=[
            {
                "prompt": "Write unit tests for notification service"
            },
            {
                "prompt": "Write integration tests for notification flow"
            }
        ]
    )

    print("\nWorkflow Result:")
    print(json.dumps(result, indent=2))

    # Example 2: Critical file refactoring
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Critical File Refactoring")
    print("=" * 80)

    refactor_result = await orch.execute_refactoring(
        target_file="backend/services/memory_service.py",
        refactor_prompt="Refactor memory service to use async/await pattern",
        test_prompt="Run unit tests for memory service"
    )

    print("\nRefactoring Result:")
    print(json.dumps(refactor_result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
