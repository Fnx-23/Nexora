"""Model-level tests for tasks."""

import pytest
from apps.tasks.models import TaskPriority, TaskStatus


@pytest.mark.django_db
def test_task_defaults(task_factory, company_factory):
    task = task_factory(company_factory(), title="Ship it")

    assert task.status == TaskStatus.TODO
    assert task.priority == TaskPriority.MEDIUM
    assert task.assignee is None
    assert task.project is None
    assert str(task) == "Ship it"
