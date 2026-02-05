"""
Ralph Wiggum Loop - Task persistence for multi-step autonomous completion.

The Ralph Wiggum pattern keeps Claude working on multi-step tasks until
completion, rather than exiting after each step. It provides:
- Task state management in /Tasks/ folder
- Completion detection via file movement to /Done/
- Iteration tracking with configurable limits
- Detailed iteration logging for debugging
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from dotenv import load_dotenv

from ..utils.logger import get_logger
from ..utils.vault_helpers import (
    get_vault_path,
    get_vault_folder,
    read_markdown_file,
    write_markdown_file,
    move_to_folder,
    generate_unique_id,
)

load_dotenv()


class TaskStatus(Enum):
    """Task status enum."""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    BLOCKED = 'blocked'
    COMPLETED = 'completed'
    FAILED = 'failed'
    MAX_ITERATIONS = 'max_iterations_reached'


@dataclass
class IterationLog:
    """Log entry for a single iteration."""
    iteration: int
    timestamp: str
    action: str
    result: str


@dataclass
class TaskState:
    """State of a Ralph Wiggum managed task."""
    task_id: str
    objective: str
    created_at: str
    status: TaskStatus = TaskStatus.PENDING
    max_iterations: int = 10
    current_iteration: int = 0
    completion_strategy: str = 'file_movement'
    steps: list[dict] = field(default_factory=list)
    completion_criteria: str = ''
    iteration_log: list[IterationLog] = field(default_factory=list)
    filepath: Optional[Path] = None

    def is_complete(self) -> bool:
        """Check if task is complete (in Done folder or marked complete)."""
        if self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.MAX_ITERATIONS):
            return True

        # Check if file was moved to Done
        if self.filepath:
            done_folder = get_vault_folder('Done')
            done_path = done_folder / self.filepath.name
            if done_path.exists():
                return True

            # Check if original file still exists
            if not self.filepath.exists():
                # File was moved somewhere
                return True

        return False

    def can_continue(self) -> bool:
        """Check if loop can continue (not complete and under max iterations)."""
        if self.is_complete():
            return False
        if self.current_iteration >= self.max_iterations:
            return False
        return True

    def increment_iteration(self, action: str, result: str):
        """Increment iteration counter and log."""
        self.current_iteration += 1
        log_entry = IterationLog(
            iteration=self.current_iteration,
            timestamp=datetime.now().strftime('%H:%M:%S'),
            action=action,
            result=result
        )
        self.iteration_log.append(log_entry)

    def to_metadata(self) -> dict:
        """Convert state to frontmatter metadata."""
        return {
            'task_id': self.task_id,
            'created_at': self.created_at,
            'status': self.status.value,
            'max_iterations': self.max_iterations,
            'current_iteration': self.current_iteration,
            'completion_strategy': self.completion_strategy,
        }

    def to_markdown_body(self) -> str:
        """Generate markdown body for task file."""
        lines = [
            f"# Task: {self.objective}",
            "",
            "## Objective",
            "",
            self.objective,
            "",
        ]

        if self.steps:
            lines.extend([
                "## Steps Required",
                "",
            ])
            for step in self.steps:
                checkbox = '[x]' if step.get('done', False) else '[ ]'
                lines.append(f"- {checkbox} {step.get('description', 'Unknown step')}")
            lines.append("")

        if self.completion_criteria:
            lines.extend([
                "## Completion Criteria",
                "",
                self.completion_criteria,
                "",
            ])

        lines.extend([
            "## Iteration Log",
            "",
            "| # | Timestamp | Action | Result |",
            "|---|-----------|--------|--------|",
        ])

        for log in self.iteration_log:
            lines.append(
                f"| {log.iteration} | {log.timestamp} | "
                f"{log.action[:30]} | {log.result[:30]} |"
            )

        lines.extend([
            "",
            "---",
            "*Managed by Ralph Wiggum Loop*",
        ])

        return '\n'.join(lines)


class RalphWiggumLoop:
    """
    Ralph Wiggum Loop - Orchestrator for multi-step task persistence.

    Manages task state files and provides the loop logic for keeping
    Claude working on tasks until completion.
    """

    def __init__(self):
        """Initialize Ralph Wiggum Loop."""
        self.logger = get_logger('RalphWiggumLoop')
        self.vault_path = get_vault_path()
        self.tasks_folder = get_vault_folder('Tasks')
        self.done_folder = get_vault_folder('Done')
        self.max_iterations = int(os.getenv('RALPH_MAX_ITERATIONS', '10'))

        self.logger.info("Ralph Wiggum Loop initialized")
        self.logger.info(f"Tasks folder: {self.tasks_folder}")
        self.logger.info(f"Default max iterations: {self.max_iterations}")

    def create_task(
        self,
        objective: str,
        steps: list[str] = None,
        completion_criteria: str = None,
        max_iterations: int = None
    ) -> TaskState:
        """
        Create a new task state file.

        Args:
            objective: Description of what the task should accomplish
            steps: List of step descriptions
            completion_criteria: Description of when task is complete
            max_iterations: Maximum iterations (default from env)

        Returns:
            TaskState object for the created task
        """
        task_id = generate_unique_id('task')
        timestamp = datetime.now()

        task = TaskState(
            task_id=task_id,
            objective=objective,
            created_at=timestamp.isoformat(),
            status=TaskStatus.IN_PROGRESS,
            max_iterations=max_iterations or self.max_iterations,
            current_iteration=0,
            completion_strategy='file_movement',
            steps=[{'description': s, 'done': False} for s in (steps or [])],
            completion_criteria=completion_criteria or 'Task file moved to /Done/ when all steps complete.',
        )

        # Add initial log entry
        task.increment_iteration('Started task', 'In progress')

        # Save to file
        filename = f"TASK_{task_id}.md"
        filepath = self.tasks_folder / filename
        task.filepath = filepath

        write_markdown_file(filepath, task.to_metadata(), task.to_markdown_body())

        self.logger.info(f"Created task: {task_id}")
        self.logger.info(f"  Objective: {objective[:50]}...")
        self.logger.info(f"  Max iterations: {task.max_iterations}")

        return task

    def load_task(self, task_id_or_path: str) -> Optional[TaskState]:
        """
        Load an existing task from file.

        Args:
            task_id_or_path: Either task ID or full path to task file

        Returns:
            TaskState object or None if not found
        """
        # Determine filepath
        if os.path.isabs(task_id_or_path):
            filepath = Path(task_id_or_path)
        else:
            # Try as task ID
            filename = f"TASK_{task_id_or_path}.md"
            filepath = self.tasks_folder / filename

            # Also check if it's just a filename
            if not filepath.exists():
                filepath = self.tasks_folder / task_id_or_path

        if not filepath.exists():
            # Check if it's in Done folder
            done_path = self.done_folder / filepath.name
            if done_path.exists():
                filepath = done_path
            else:
                self.logger.warning(f"Task file not found: {filepath}")
                return None

        try:
            metadata, body = read_markdown_file(filepath)

            # Parse task state from metadata
            task = TaskState(
                task_id=metadata.get('task_id', filepath.stem),
                objective=self._extract_objective(body),
                created_at=metadata.get('created_at', ''),
                status=TaskStatus(metadata.get('status', 'in_progress')),
                max_iterations=metadata.get('max_iterations', self.max_iterations),
                current_iteration=metadata.get('current_iteration', 0),
                completion_strategy=metadata.get('completion_strategy', 'file_movement'),
                steps=self._extract_steps(body),
                completion_criteria=self._extract_criteria(body),
                iteration_log=self._extract_iteration_log(body),
                filepath=filepath,
            )

            return task

        except Exception as e:
            self.logger.error(f"Failed to load task: {e}")
            return None

    def _extract_objective(self, body: str) -> str:
        """Extract objective from markdown body."""
        import re
        match = re.search(r'## Objective\n\n(.+?)(?=\n\n##|\Z)', body, re.DOTALL)
        return match.group(1).strip() if match else ''

    def _extract_steps(self, body: str) -> list[dict]:
        """Extract steps from markdown body."""
        import re
        steps = []
        match = re.search(r'## Steps Required\n\n(.*?)(?=\n\n##|\Z)', body, re.DOTALL)
        if match:
            for line in match.group(1).split('\n'):
                step_match = re.match(r'- \[([ x])\] (.+)', line)
                if step_match:
                    steps.append({
                        'done': step_match.group(1) == 'x',
                        'description': step_match.group(2)
                    })
        return steps

    def _extract_criteria(self, body: str) -> str:
        """Extract completion criteria from markdown body."""
        import re
        match = re.search(r'## Completion Criteria\n\n(.+?)(?=\n\n##|\Z)', body, re.DOTALL)
        return match.group(1).strip() if match else ''

    def _extract_iteration_log(self, body: str) -> list[IterationLog]:
        """Extract iteration log from markdown body."""
        import re
        logs = []
        # Find table rows
        pattern = r'\| (\d+) \| ([\d:]+) \| (.+?) \| (.+?) \|'
        for match in re.finditer(pattern, body):
            logs.append(IterationLog(
                iteration=int(match.group(1)),
                timestamp=match.group(2),
                action=match.group(3).strip(),
                result=match.group(4).strip()
            ))
        return logs

    def save_task(self, task: TaskState):
        """
        Save task state back to file.

        Args:
            task: TaskState to save
        """
        if not task.filepath:
            self.logger.error("Cannot save task: no filepath set")
            return

        write_markdown_file(task.filepath, task.to_metadata(), task.to_markdown_body())
        self.logger.debug(f"Saved task: {task.task_id}")

    def check_completion(self, task: TaskState) -> bool:
        """
        Check if a task is complete.

        Checks:
        1. If status is already complete/failed
        2. If task file has been moved to /Done/
        3. If max iterations reached

        Args:
            task: TaskState to check

        Returns:
            True if complete, False if can continue
        """
        # Check if already marked complete
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            self.logger.info(f"Task {task.task_id} is {task.status.value}")
            return True

        # Check if file moved to Done
        if task.filepath:
            done_path = self.done_folder / task.filepath.name
            if done_path.exists():
                self.logger.info(f"Task {task.task_id} found in Done folder")
                task.status = TaskStatus.COMPLETED
                return True

            # Check if original file no longer exists (moved somewhere)
            if not task.filepath.exists():
                self.logger.info(f"Task {task.task_id} file no longer at original location")
                return True

        # Check max iterations
        if task.current_iteration >= task.max_iterations:
            self.logger.warning(
                f"Task {task.task_id} reached max iterations ({task.max_iterations})"
            )
            task.status = TaskStatus.MAX_ITERATIONS
            self.save_task(task)
            return True

        return False

    def record_iteration(self, task: TaskState, action: str, result: str):
        """
        Record an iteration in the task log.

        Args:
            task: TaskState to update
            action: Description of what was done
            result: Result of the action
        """
        task.increment_iteration(action, result)
        self.save_task(task)

    def complete_task(self, task: TaskState, success: bool = True):
        """
        Mark a task as complete and move to Done folder.

        Args:
            task: TaskState to complete
            success: Whether task completed successfully
        """
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        self.save_task(task)

        if task.filepath and task.filepath.exists():
            move_to_folder(task.filepath, 'Done')
            self.logger.info(f"Task {task.task_id} completed and moved to Done")

    def get_pending_tasks(self) -> list[TaskState]:
        """
        Get all pending/in-progress tasks.

        Returns:
            List of TaskState objects
        """
        tasks = []
        for task_file in self.tasks_folder.glob('TASK_*.md'):
            task = self.load_task(str(task_file))
            if task and task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
                tasks.append(task)
        return tasks

    def should_continue(self, task: TaskState) -> dict:
        """
        Check if the Ralph Wiggum loop should continue for a task.

        This is the core stop hook logic - determines whether to allow
        exit or re-inject the prompt for another iteration.

        Args:
            task: TaskState to check

        Returns:
            Dict with 'continue' bool and 'reason' string
        """
        # Reload task to get latest state
        reloaded = self.load_task(task.task_id)
        if not reloaded:
            return {'continue': False, 'reason': 'Task not found'}

        # Check completion
        if self.check_completion(reloaded):
            return {
                'continue': False,
                'reason': f'Task {reloaded.status.value}'
            }

        # Can continue
        return {
            'continue': True,
            'reason': f'Iteration {reloaded.current_iteration}/{reloaded.max_iterations}'
        }


# Convenience functions
def create_task(
    objective: str,
    steps: list[str] = None,
    completion_criteria: str = None,
    max_iterations: int = None
) -> TaskState:
    """Create a new task. Convenience function."""
    loop = RalphWiggumLoop()
    return loop.create_task(objective, steps, completion_criteria, max_iterations)


def get_task(task_id_or_path: str) -> Optional[TaskState]:
    """Load an existing task. Convenience function."""
    loop = RalphWiggumLoop()
    return loop.load_task(task_id_or_path)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Ralph Wiggum Loop - Multi-step task management'
    )
    parser.add_argument(
        '--create',
        metavar='OBJECTIVE',
        help='Create a new task with given objective'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List pending tasks'
    )
    parser.add_argument(
        '--check',
        metavar='TASK_ID',
        help='Check if task should continue'
    )

    args = parser.parse_args()

    loop = RalphWiggumLoop()

    if args.create:
        task = loop.create_task(args.create)
        print(f"Created task: {task.task_id}")
        print(f"File: {task.filepath}")
    elif args.list:
        tasks = loop.get_pending_tasks()
        print(f"=== Pending Tasks: {len(tasks)} ===")
        for task in tasks:
            print(f"  - {task.task_id}: {task.objective[:40]}...")
            print(f"    Iteration: {task.current_iteration}/{task.max_iterations}")
    elif args.check:
        task = loop.load_task(args.check)
        if task:
            result = loop.should_continue(task)
            print(f"Task: {task.task_id}")
            print(f"Continue: {result['continue']}")
            print(f"Reason: {result['reason']}")
        else:
            print(f"Task not found: {args.check}")
    else:
        print("Ralph Wiggum Loop")
        print("Use --create, --list, or --check")
