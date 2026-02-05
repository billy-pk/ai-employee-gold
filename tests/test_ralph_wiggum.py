"""Tests for the Ralph Wiggum Loop module."""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from src.hooks.ralph_wiggum import (
    RalphWiggumLoop,
    TaskState,
    TaskStatus,
    IterationLog,
    create_task,
    get_task,
)


class TestTaskState:
    """Test cases for TaskState dataclass."""

    def test_default_values(self):
        """Test TaskState default values."""
        task = TaskState(
            task_id='test_123',
            objective='Test objective',
            created_at='2026-02-05T10:00:00Z'
        )

        assert task.status == TaskStatus.PENDING
        assert task.max_iterations == 10
        assert task.current_iteration == 0
        assert task.steps == []
        assert task.iteration_log == []

    def test_is_complete_by_status(self):
        """Test is_complete with completed status."""
        task = TaskState(
            task_id='test_123',
            objective='Test',
            created_at='',
            status=TaskStatus.COMPLETED
        )
        assert task.is_complete() is True

    def test_is_complete_by_failed_status(self):
        """Test is_complete with failed status."""
        task = TaskState(
            task_id='test_123',
            objective='Test',
            created_at='',
            status=TaskStatus.FAILED
        )
        assert task.is_complete() is True

    def test_is_complete_in_progress(self):
        """Test is_complete with in_progress status."""
        task = TaskState(
            task_id='test_123',
            objective='Test',
            created_at='',
            status=TaskStatus.IN_PROGRESS
        )
        assert task.is_complete() is False

    def test_can_continue_under_limit(self):
        """Test can_continue under iteration limit."""
        task = TaskState(
            task_id='test_123',
            objective='Test',
            created_at='',
            status=TaskStatus.IN_PROGRESS,
            max_iterations=10,
            current_iteration=5
        )
        assert task.can_continue() is True

    def test_can_continue_at_limit(self):
        """Test can_continue at iteration limit."""
        task = TaskState(
            task_id='test_123',
            objective='Test',
            created_at='',
            status=TaskStatus.IN_PROGRESS,
            max_iterations=10,
            current_iteration=10
        )
        assert task.can_continue() is False

    def test_increment_iteration(self):
        """Test iteration incrementing."""
        task = TaskState(
            task_id='test_123',
            objective='Test',
            created_at=''
        )

        task.increment_iteration('Action 1', 'Success')
        assert task.current_iteration == 1
        assert len(task.iteration_log) == 1
        assert task.iteration_log[0].action == 'Action 1'

    def test_to_metadata(self):
        """Test metadata generation."""
        task = TaskState(
            task_id='test_123',
            objective='Test',
            created_at='2026-02-05T10:00:00Z',
            status=TaskStatus.IN_PROGRESS,
            max_iterations=5,
            current_iteration=2
        )

        metadata = task.to_metadata()
        assert metadata['task_id'] == 'test_123'
        assert metadata['status'] == 'in_progress'
        assert metadata['max_iterations'] == 5
        assert metadata['current_iteration'] == 2

    def test_to_markdown_body(self):
        """Test markdown body generation."""
        task = TaskState(
            task_id='test_123',
            objective='Complete the task',
            created_at='',
            steps=[
                {'description': 'Step 1', 'done': True},
                {'description': 'Step 2', 'done': False}
            ],
            completion_criteria='All steps done'
        )
        task.increment_iteration('Started', 'In progress')

        body = task.to_markdown_body()

        assert '# Task: Complete the task' in body
        assert '- [x] Step 1' in body
        assert '- [ ] Step 2' in body
        assert 'All steps done' in body
        assert '| 1 |' in body
        assert 'Started' in body


class TestRalphWiggumLoop:
    """Test cases for RalphWiggumLoop class."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Tasks').mkdir()
            (vault / 'Done').mkdir()
            (vault / 'Logs').mkdir()
            yield vault

    @pytest.fixture
    def loop(self, temp_vault, monkeypatch):
        """Create a RalphWiggumLoop with temp vault."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))
        monkeypatch.setenv('RALPH_MAX_ITERATIONS', '10')
        return RalphWiggumLoop()

    def test_initialization(self, loop, temp_vault):
        """Test RalphWiggumLoop initializes correctly."""
        assert loop.vault_path == temp_vault
        assert loop.max_iterations == 10
        assert loop.tasks_folder == temp_vault / 'Tasks'
        assert loop.done_folder == temp_vault / 'Done'

    def test_create_task(self, loop):
        """Test task creation."""
        task = loop.create_task(
            objective='Test objective',
            steps=['Step 1', 'Step 2'],
            max_iterations=5
        )

        assert task.task_id.startswith('task_')
        assert task.objective == 'Test objective'
        assert task.max_iterations == 5
        assert len(task.steps) == 2
        assert task.filepath.exists()
        assert task.current_iteration == 1  # Initial log entry

    def test_load_task(self, loop):
        """Test loading an existing task."""
        # Create a task
        original = loop.create_task(
            objective='Load test',
            steps=['A', 'B']
        )

        # Load it
        loaded = loop.load_task(original.task_id)

        assert loaded is not None
        assert loaded.task_id == original.task_id
        assert loaded.objective == 'Load test'
        assert len(loaded.steps) == 2

    def test_load_task_by_path(self, loop):
        """Test loading task by file path."""
        task = loop.create_task(objective='Path test')
        loaded = loop.load_task(str(task.filepath))

        assert loaded is not None
        assert loaded.task_id == task.task_id

    def test_load_task_not_found(self, loop):
        """Test loading non-existent task."""
        loaded = loop.load_task('nonexistent_task')
        assert loaded is None

    def test_save_task(self, loop):
        """Test saving task changes."""
        task = loop.create_task(objective='Save test')
        task.current_iteration = 5
        task.increment_iteration('Test action', 'Test result')

        loop.save_task(task)

        # Reload and verify
        loaded = loop.load_task(task.task_id)
        assert loaded.current_iteration == 6  # 5 + 1 from increment

    def test_check_completion_not_complete(self, loop):
        """Test completion check for incomplete task."""
        task = loop.create_task(
            objective='Incomplete',
            max_iterations=10
        )

        assert loop.check_completion(task) is False

    def test_check_completion_max_iterations(self, loop):
        """Test completion check at max iterations."""
        task = loop.create_task(
            objective='Max iterations',
            max_iterations=5
        )
        task.current_iteration = 5  # At max

        assert loop.check_completion(task) is True
        assert task.status == TaskStatus.MAX_ITERATIONS

    def test_check_completion_in_done_folder(self, loop, temp_vault):
        """Test completion check when file in Done folder."""
        task = loop.create_task(objective='Done test')

        # Move file to Done
        import shutil
        shutil.move(str(task.filepath), str(loop.done_folder / task.filepath.name))

        assert loop.check_completion(task) is True
        assert task.status == TaskStatus.COMPLETED

    def test_record_iteration(self, loop):
        """Test recording an iteration."""
        task = loop.create_task(objective='Record test')
        initial_iteration = task.current_iteration

        loop.record_iteration(task, 'Did something', 'It worked')

        loaded = loop.load_task(task.task_id)
        assert loaded.current_iteration == initial_iteration + 1
        assert loaded.iteration_log[-1].action == 'Did something'

    def test_complete_task(self, loop, temp_vault):
        """Test completing a task."""
        task = loop.create_task(objective='Complete test')

        loop.complete_task(task, success=True)

        # Should be in Done folder
        done_path = loop.done_folder / task.filepath.name
        assert done_path.exists()
        assert not task.filepath.exists()

    def test_complete_task_failed(self, loop, temp_vault):
        """Test completing a task as failed."""
        task = loop.create_task(objective='Fail test')

        loop.complete_task(task, success=False)

        # File should be in Done folder with failed status
        done_path = loop.done_folder / task.filepath.name
        assert done_path.exists()

        # Load from Done folder
        loaded = loop.load_task(str(done_path))
        assert loaded is not None
        assert loaded.status == TaskStatus.FAILED

    def test_get_pending_tasks(self, loop):
        """Test getting pending tasks."""
        # Create multiple tasks
        loop.create_task(objective='Task 1')
        loop.create_task(objective='Task 2')
        task3 = loop.create_task(objective='Task 3')
        task3.status = TaskStatus.COMPLETED
        loop.save_task(task3)

        pending = loop.get_pending_tasks()

        # Should find 2 (task3 is completed)
        assert len(pending) == 2

    def test_should_continue_can_continue(self, loop):
        """Test should_continue when can continue."""
        task = loop.create_task(objective='Continue test', max_iterations=10)

        result = loop.should_continue(task)

        assert result['continue'] is True
        assert '1/10' in result['reason']

    def test_should_continue_max_iterations(self, loop):
        """Test should_continue at max iterations."""
        task = loop.create_task(objective='Max test', max_iterations=1)

        result = loop.should_continue(task)

        assert result['continue'] is False
        assert 'max_iterations' in result['reason'].lower()


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Tasks').mkdir()
            (vault / 'Done').mkdir()
            (vault / 'Logs').mkdir()
            yield vault

    def test_create_task_convenience(self, temp_vault, monkeypatch):
        """Test create_task convenience function."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        task = create_task('Convenience test')

        assert task is not None
        assert task.objective == 'Convenience test'
        assert task.filepath.exists()

    def test_get_task_convenience(self, temp_vault, monkeypatch):
        """Test get_task convenience function."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        original = create_task('Get test')
        loaded = get_task(original.task_id)

        assert loaded is not None
        assert loaded.task_id == original.task_id


class TestIterationLog:
    """Test IterationLog dataclass."""

    def test_iteration_log_creation(self):
        """Test creating an iteration log entry."""
        log = IterationLog(
            iteration=1,
            timestamp='10:30:00',
            action='Test action',
            result='Success'
        )

        assert log.iteration == 1
        assert log.timestamp == '10:30:00'
        assert log.action == 'Test action'
        assert log.result == 'Success'
