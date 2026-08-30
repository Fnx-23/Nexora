import { useCallback, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { PageHeader } from "@/components/layout/PageHeader"
import { DocumentManager } from "@/components/DocumentManager"
import { Button } from "@/components/ui/Button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { Modal } from "@/components/ui/Modal"
import { StatusBadge } from "@/components/ui/Badge"
import { ErrorState } from "@/components/ui/ErrorState"
import { LoadingState } from "@/components/ui/LoadingState"
import { useAuth } from "@/hooks/useAuth"
import {
  fetchProject,
  updateProject,
  archiveProject,
  deleteProject,
  type CreateProjectPayload,
} from "@/features/projects/api"
import { fetchCustomers } from "@/features/customers/api"
import { fetchMembers } from "@/features/team/api"
import { queryKeys } from "@/utils/queryKeys"

const STATUS_OPTIONS = ["PLANNING", "IN_PROGRESS", "ON_HOLD", "COMPLETED"]
const PRIORITY_OPTIONS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline">
      <span className="w-32 shrink-0 text-sm font-medium text-slate-500">{label}</span>
      <span className="text-sm text-slate-900">{children}</span>
    </div>
  )
}

export function ProjectDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { activeCompany, role } = useAuth()
  const queryClient = useQueryClient()
  const companyId = activeCompany?.id ?? null

  const canEdit = role === "ADMIN" || role === "MANAGER" || role === "EMPLOYEE"
  const canDelete = role === "ADMIN" || role === "MANAGER"

  const [editOpen, setEditOpen] = useState(false)
  const [form, setForm] = useState<Partial<CreateProjectPayload>>({})
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [formGlobalError, setFormGlobalError] = useState<string | null>(null)

  const [archiveOpen, setArchiveOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)

  const projectQuery = useQuery({
    queryKey: queryKeys.project(id!),
    queryFn: () => fetchProject(id!),
    enabled: id !== undefined,
  })

  const customersQuery = useQuery({
    queryKey: queryKeys.customers(companyId),
    queryFn: () => fetchCustomers({ page_size: 100 }),
    enabled: companyId !== null && editOpen,
  })

  const membersQuery = useQuery({
    queryKey: queryKeys.members(companyId),
    queryFn: fetchMembers,
    enabled: companyId !== null && editOpen,
  })

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.projects(companyId) })
    void queryClient.invalidateQueries({ queryKey: queryKeys.project(id!) })
  }, [queryClient, companyId, id])

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<CreateProjectPayload>) => updateProject(id!, payload),
    onSuccess: () => { invalidate(); closeEdit() },
    onError: (err: Error & { response?: { data?: Record<string, unknown> } }) => {
      const data = err.response?.data
      if (data && typeof data === "object") {
        const fieldErrors: Record<string, string> = {}
        for (const [key, val] of Object.entries(data)) {
          if (key === "detail") setFormGlobalError(String(val))
          else if (Array.isArray(val)) fieldErrors[key] = val.join(" ")
          else if (typeof val === "string") fieldErrors[key] = val
        }
        if (Object.keys(fieldErrors).length) setFormErrors(fieldErrors)
      } else {
        setFormGlobalError("An unexpected error occurred.")
      }
    },
  })

  const archiveMutation = useMutation({
    mutationFn: archiveProject,
    onSuccess: () => { invalidate(); setArchiveOpen(false) },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      // The project is gone; cancel any queued refetch and remove its cached
      // query rather than invalidating it, otherwise TanStack refetches the
      // (now deleted) resource and returns a spurious 404 right after delete
      // (BUG-3).
      const key = queryKeys.project(id!)
      void queryClient.cancelQueries({ queryKey: key })
      queryClient.removeQueries({ queryKey: key })
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects(companyId) })
      navigate("/projects")
    },
  })

  const project = projectQuery.data

  function openEdit() {
    if (!project) return
    setForm({
      name: project.name,
      description: project.description,
      customer: project.customer,
      manager: project.manager,
      status: project.status,
      priority: project.priority,
      start_date: project.start_date,
      deadline: project.deadline,
    })
    setFormErrors({})
    setFormGlobalError(null)
    setEditOpen(true)
  }

  function closeEdit() {
    setEditOpen(false)
    setFormErrors({})
    setFormGlobalError(null)
  }

  function handleSave(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name?.trim()) {
      setFormErrors({ name: "Project name is required." })
      return
    }
    updateMutation.mutate(form)
  }

  return (
    <div>
      <PageHeader
        title={project?.name ?? "Project"}
        description={project ? `Created ${formatDate(project.created_at)}` : undefined}
        actions={
          project && (
            <div className="flex gap-2">
              {canEdit && <Button onClick={openEdit}>Edit</Button>}
              {canDelete && project.status !== "ARCHIVED" && (
                <Button variant="secondary" onClick={() => setArchiveOpen(true)}>
                  Archive
                </Button>
              )}
              {canDelete && (
                <Button variant="danger" onClick={() => setDeleteOpen(true)}>
                  Delete
                </Button>
              )}
            </div>
          )
        }
      />

      {projectQuery.isPending && <LoadingState label="Loading project…" />}

      {projectQuery.isError && (
        <ErrorState
          title="Could not load project"
          description="The project may not exist or you may not have access."
          action={<Button onClick={() => navigate("/projects")}>Back to projects</Button>}
        />
      )}

      {project && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <InfoRow label="Customer">{project.customer_name || "—"}</InfoRow>
              <InfoRow label="Manager">{project.manager_name || "—"}</InfoRow>
              <InfoRow label="Status"><StatusBadge value={project.status} /></InfoRow>
              <InfoRow label="Priority"><StatusBadge value={project.priority} /></InfoRow>
              <InfoRow label="Start date">{project.start_date ? formatDate(project.start_date) : "—"}</InfoRow>
              <InfoRow label="Deadline">{project.deadline ? formatDate(project.deadline) : "—"}</InfoRow>
              {project.description && (
                <div className="pt-2">
                  <p className="text-sm font-medium text-slate-500">Description</p>
                  <p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{project.description}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <DocumentManager
            entityKind="PROJECT"
            entityId={project.id}
            canDelete={canDelete}
          />
        </div>
      )}

      {/* Edit Modal */}
      <Modal
        open={editOpen}
        onClose={closeEdit}
        title="Edit project"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={closeEdit}>Cancel</Button>
            <Button
              type="submit"
              form="project-edit-form"
              isLoading={updateMutation.isPending}
            >
              Save changes
            </Button>
          </>
        }
      >
        <form id="project-edit-form" onSubmit={handleSave} className="space-y-4">
          {formGlobalError && (
            <div role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {formGlobalError}
            </div>
          )}
          <Input
            label="Project name"
            value={form.name ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            error={formErrors.name}
            required
          />
          <div>
            <label htmlFor="edit-desc" className="mb-1.5 block text-sm font-medium text-slate-700">
              Description
            </label>
            <textarea
              id="edit-desc"
              rows={3}
              value={form.description ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-0"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="Customer"
              value={form.customer ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, customer: e.target.value || null }))}
            >
              <option value="">No customer</option>
              {customersQuery.data?.results.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </Select>
            <Select
              label="Manager"
              value={form.manager ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, manager: e.target.value || null }))}
            >
              <option value="">No manager</option>
              {membersQuery.data?.map((m) => (
                <option key={m.id} value={m.id}>{m.full_name || m.email}</option>
              ))}
            </Select>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="Status"
              value={form.status ?? "PLANNING"}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              error={formErrors.status}
            >
              {STATUS_OPTIONS.map((v) => (
                <option key={v} value={v}>{v.replace("_", " ")}</option>
              ))}
            </Select>
            <Select
              label="Priority"
              value={form.priority ?? "MEDIUM"}
              onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
              error={formErrors.priority}
            >
              {PRIORITY_OPTIONS.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </Select>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Start date"
              type="date"
              value={form.start_date ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value || null }))}
            />
            <Input
              label="Deadline"
              type="date"
              value={form.deadline ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, deadline: e.target.value || null }))}
            />
          </div>
        </form>
      </Modal>

      {/* Archive Confirmation */}
      <Modal
        open={archiveOpen}
        onClose={() => setArchiveOpen(false)}
        title="Archive project"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setArchiveOpen(false)}>Cancel</Button>
            <Button
              variant="danger"
              isLoading={archiveMutation.isPending}
              onClick={() => archiveMutation.mutate(id!)}
            >
              Archive
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          This will set the project status to <span className="font-medium">Archived</span>.
        </p>
      </Modal>

      {/* Delete Confirmation */}
      <Modal
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Delete project"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button
              variant="danger"
              isLoading={deleteMutation.isPending}
              onClick={() => deleteMutation.mutate(id!)}
            >
              Delete permanently
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          Are you sure you want to permanently delete{" "}
          <span className="font-medium text-slate-900">{project?.name}</span>?
          This action cannot be undone.
        </p>
      </Modal>
    </div>
  )
}
