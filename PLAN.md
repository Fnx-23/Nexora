# Nexora Reports — Implementation Plan

## Context
Nexora currently has a Dashboard with basic KPIs and status distributions but no dedicated reporting feature. The user wants six business reports backed by real database data, with efficient aggregation, tenant scoping, and full test coverage.

## Architecture
- **Single endpoint:** `GET /api/v1/reports/` — one APIView (matching Dashboard pattern), all report data returned in one response, filtered by optional query params
- **Frontend charts:** CSS horizontal bars only (matching DashboardPage `StatusBars` pattern), no new dependencies
- **All data tenant-scoped** via `request.company`

---

## Backend

### 1. Create `apps/core/api/reports.py` — ReportsView (APIView)

```
GET /api/v1/reports/?date_from=&date_to=&project=&assignee=
```

Query params (all optional):
- `date_from` / `date_to` — ISO date strings. Applied to `Project.created_at`, `Task.created_at`, `TimeEntry.date`
- `project` — UUID. Filters tasks and time entries by project
- `assignee` — UUID. Filters tasks (by assignee) and time entries (by user)

Response structure:
```json
{
  "summary": {
    "total_projects": 10,
    "total_tasks": 50,
    "total_time_entries": 100,
    "total_hours_logged": 420.5,
    "active_team_members": 5
  },
  "project_performance": {
    "by_status": [{"status": "PLANNING", "label": "Planning", "count": 2}, ...],
    "by_priority": [{"priority": "HIGH", "label": "High", "count": 3}, ...],
    "completion_rate": 0.65
  },
  "task_completion": {
    "by_status": [...],
    "by_priority": [...],
    "completion_rate": 0.72,
    "overdue_count": 5,
    "completed_last_30_days": 12
  },
  "team_workload": [
    {
      "user_id": "uuid",
      "name": "John Doe",
      "tasks_assigned": 8,
      "tasks_completed": 5,
      "hours_logged": 40.5,
      "entries_count": 15
    }
  ],
  "time_by_project": [
    {"project_id": "uuid", "project_name": "Website", "total_hours": 120.5, "entry_count": 45}
  ],
  "overdue_tasks": {
    "total": 5,
    "by_project": [{"project_name": "...", "count": 2}],
    "by_assignee": [{"name": "...", "count": 3}],
    "tasks": [{"id": "uuid", "title": "...", "project_name": "...", "assignee_name": "...", "due_date": "2025-01-15", "priority": "HIGH"}]
  }
}
```

Key implementation details:
- `ProjectPerformance.by_status` — `Project.objects.filter(company=company, **date_filters).values("status").annotate(count=Count("id"))`
- `ProjectPerformance.by_priority` — Same with `"priority"`
- `ProjectPerformance.completion_rate` — count COMPLETED / total (excluding ARCHIVED)
- `TaskCompletion.by_status` — `Task.objects.filter(company=company, **filters).values("status").annotate(count=Count("id"))`
- `TaskCompletion.overdue_count` — `Task.objects.filter(company=company, due_date__lt=today, status__in=[TODO, IN_PROGRESS, IN_REVIEW]).count()`
- `TaskCompletion.completed_last_30_days` — `Task.objects.filter(company=company, status=DONE, updated_at__gte=thirty_days_ago).count()`
- `TeamWorkload` — Aggregate tasks + time entries per user via `values("assignee").annotate(...)` and `values("user").annotate(...)`, then merge by user ID
- `TimeByProject` — `TimeEntry.objects.filter(company=company, **filters).values("project__id", "project__name").annotate(total=Sum("duration"), count=Count("id"))`
- `OverdueTasks.tasks` — Query actual Task objects with `select_related("project", "assignee")`, limited to top 50
- `OverdueTasks.by_project` — `values("project__name").annotate(count=Count("id"))`
- `OverdueTasks.by_assignee` — `values("assignee__first_name", "assignee__last_name").annotate(count=Count("id"))`
- Duration conversion: `timedelta.total_seconds() / 3600` for hours
- All queries use `.filter(company=company)` for tenant scoping
- `date_from`/`date_to` applied to `created_at__gte`/`created_at__lte` for projects/tasks, `date__gte`/`date__lte` for time entries

### 2. Register URL in `config/urls.py`

```python
path("reports/", ReportsView.as_view(), name="reports"),
```

### 3. Tests — `tests/core/test_reports.py`

Test classes:
- `TestSummary` — Verify counts for projects, tasks, time entries, hours, team members
- `TestProjectPerformance` — Status/priority distributions, completion rate
- `TestTaskCompletion` — Status/priority distributions, overdue count, completed_last_30_days
- `TestTeamWorkload` — Per-member task/hour aggregations
- `TestTimeByProject` — Per-project hour aggregations
- `TestOverdueTasks` — Overdue detection, by_project, by_assignee breakdowns
- `TestFiltering` — date_from, date_to, project, assignee params
- `TestTenantIsolation` — Company A cannot see Company B data, unauthenticated returns 401, no membership returns 403
- `TestPermissions` — All authenticated members can view reports (no role restriction for reading)

Target: ~30 tests

---

## Frontend

### 4. Create `src/types/reports.ts`

TypeScript interfaces matching the backend response.

### 5. Create `src/features/reports/api.ts`

```typescript
export interface ReportsParams {
  date_from?: string
  date_to?: string
  project?: string
  assignee?: string
}

export async function fetchReports(params: ReportsParams = {}): Promise<ReportsData> {
  const { data } = await api.get<ReportsData>("/reports/", { params })
  return data
}
```

### 6. Add query key to `src/utils/queryKeys.ts`

```typescript
reports: (companyId: string | null) => ["reports", companyId] as const,
```

### 7. Add `BarChartIcon` to `src/components/icons.tsx`

SVG bar chart icon (3 vertical bars of different heights).

### 8. Create `src/pages/ReportsPage.tsx`

Layout (top to bottom):
1. **PageHeader** — "Reports" title + description
2. **Filter bar** — date_from, date_to, project select, assignee select (team members). All filters update the query params
3. **Summary cards** — 5 KPI cards: Total Projects, Total Tasks, Hours Logged, Team Members, Overdue Tasks (danger-highlighted)
4. **Project Performance** — Horizontal stacked status bar (same as Dashboard) + priority bar
5. **Task Completion** — Horizontal stacked status bar + priority bar + completion rate + overdue count
6. **Team Workload** — Table: Name | Tasks Assigned | Tasks Completed | Hours Logged | Entries
7. **Time by Project** — Horizontal bar chart (one row per project, bar proportional to hours)
8. **Overdue Tasks** — Table: Title | Project | Assignee | Due Date | Priority (with StatusBadge)

Sub-components (defined in same file, matching DashboardPage pattern):
- `ReportsSkeleton` — Loading skeleton
- `MetricCard` — Summary card (reuse KpiCard pattern)
- `HorizontalBarChart` — Generic labeled horizontal bar chart
- `ReportTable` — Styled table for report data

Data dependencies for filters:
- Projects list: `fetchProjects({ page_size: 100 })` via `queryKeys.projects`
- Team members: `fetchMembers()` via `queryKeys.members`

### 9. Add route and nav item

- `src/App.tsx`: `<Route path="/reports" element={<ReportsPage />} />`
- `src/components/layout/Sidebar.tsx`: Add `{ to: "/reports", label: "Reports", icon: BarChartIcon }` after Dashboard

### 10. Tests — `src/pages/__tests__/ReportsPage.test.tsx`

Tests:
- Loading state shown while data fetches
- Summary cards render with correct values
- Project performance bars render
- Task completion bars render
- Team workload table renders with member data
- Time by project bars render
- Overdue tasks table renders
- Empty state when no data
- Error state on fetch failure
- Filter interactions (project select, date inputs)
- Employee role can view reports

Target: ~18 tests

---

## File Changes Summary

### New files
| File | Purpose |
|---|---|
| `backend/apps/core/api/reports.py` | ReportsView — single aggregation endpoint |
| `backend/tests/core/test_reports.py` | ~30 backend tests |
| `frontend/src/types/reports.ts` | TypeScript interfaces |
| `frontend/src/features/reports/api.ts` | API fetcher |
| `frontend/src/pages/ReportsPage.tsx` | Reports page with filters, charts, tables |
| `frontend/src/pages/__tests__/ReportsPage.test.tsx` | ~18 frontend tests |

### Modified files
| File | Change |
|---|---|
| `backend/config/urls.py` | Register `reports/` URL |
| `frontend/src/utils/queryKeys.ts` | Add `reports` key |
| `frontend/src/components/icons.tsx` | Add `BarChartIcon` |
| `frontend/src/components/layout/Sidebar.tsx` | Add Reports nav item |
| `frontend/src/App.tsx` | Add `/reports` route |

---

## Verification

```bash
# Backend
cd backend
../.venv/bin/ruff check apps/core/api/reports.py tests/core/test_reports.py
../.venv/bin/ruff format --check apps/core/api/reports.py tests/core/test_reports.py
../.venv/bin/python -m pytest tests/core/test_reports.py -v

# Frontend
cd frontend
npx eslint src/pages/ReportsPage.tsx src/features/reports/api.ts src/types/reports.ts
npx tsc --noEmit
npx vitest run src/pages/__tests__/ReportsPage.test.tsx

# Full suite
../.venv/bin/python -m pytest tests/ -v
npx vitest run
```
