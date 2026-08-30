"""Model-level tests for projects."""

import pytest
from apps.projects.models import ProjectStatus


@pytest.mark.django_db
def test_project_defaults(project_factory, company_factory):
    project = project_factory(company_factory())

    assert project.status == ProjectStatus.PLANNING
    assert project.customer is None
    assert str(project) == project.name


@pytest.mark.django_db
def test_project_status_choices_cover_documented_workflow():
    expected = {"PLANNING", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "ARCHIVED"}
    assert {choice for choice, _ in ProjectStatus.choices} == expected
