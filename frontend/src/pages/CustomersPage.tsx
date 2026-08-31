import { useCallback, useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { PageHeader } from "@/components/layout/PageHeader"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { StatusBadge } from "@/components/ui/Badge"
import { Modal } from "@/components/ui/Modal"
import { ErrorState } from "@/components/ui/ErrorState"
import { EmptyState } from "@/components/ui/EmptyState"
import { LoadingState } from "@/components/ui/LoadingState"
import {
  Table,
  TableContainer,
  TBody,
  TD,
  TH,
  THead,
  TR,
} from "@/components/ui/Table"
import { useAuth } from "@/hooks/useAuth"
import {
  fetchCustomers,
  createCustomer,
  updateCustomer,
  archiveCustomer,
  type CustomerListParams,
  type CreateCustomerPayload,
} from "@/features/customers/api"
import { queryKeys } from "@/utils/queryKeys"

const PAGE_SIZE = 25

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "ACTIVE", label: "Active" },
  { value: "INACTIVE", label: "Inactive" },
  { value: "ARCHIVED", label: "Archived" },
]

const EMPTY_FORM: CreateCustomerPayload = {
  name: "",
  company_name: "",
  email: "",
  phone: "",
  address: "",
  notes: "",
  status: "ACTIVE",
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export function CustomersPage() {
  const { activeCompany, role } = useAuth()
  const queryClient = useQueryClient()
  const companyId = activeCompany?.id ?? null

  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("")
  const [page, setPage] = useState(1)

  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<CreateCustomerPayload>({ ...EMPTY_FORM })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [formGlobalError, setFormGlobalError] = useState<string | null>(null)

  const [archiveTarget, setArchiveTarget] = useState<{ id: string; name: string } | null>(null)

  const canDelete = role === "ADMIN" || role === "MANAGER"

  const queryParams = useMemo<CustomerListParams>(() => {
    const params: CustomerListParams = { page, page_size: PAGE_SIZE }
    if (debouncedSearch) params.search = debouncedSearch
    if (statusFilter) params.status = statusFilter
    return params
  }, [page, debouncedSearch, statusFilter])

  const customersQuery = useQuery({
    queryKey: [...queryKeys.customers(companyId), queryParams],
    queryFn: () => fetchCustomers(queryParams),
    enabled: companyId !== null,
  })

  const searchTimeout = useMemo(() => {
    let timer: ReturnType<typeof setTimeout>
    return (value: string) => {
      clearTimeout(timer)
      timer = setTimeout(() => {
        setDebouncedSearch(value)
        setPage(1)
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [])

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearch(e.target.value)
      searchTimeout(e.target.value)
    },
    [searchTimeout],
  )

  const handleStatusChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value)
    setPage(1)
  }, [])

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.customers(companyId) })
  }, [queryClient, companyId])

  const createMutation = useMutation({
    mutationFn: createCustomer,
    onSuccess: () => { invalidate(); closeForm() },
    onError: (err: Error & { response?: { data?: Record<string, unknown> } }) => {
      handleMutationError(err)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateCustomerPayload> }) =>
      updateCustomer(id, payload),
    onSuccess: () => { invalidate(); closeForm() },
    onError: (err: Error & { response?: { data?: Record<string, unknown> } }) => {
      handleMutationError(err)
    },
  })

  const archiveMutation = useMutation({
    mutationFn: archiveCustomer,
    onSuccess: () => { invalidate(); setArchiveTarget(null) },
  })

  function handleMutationError(err: Error & { response?: { data?: Record<string, unknown> } }) {
    const data = err.response?.data
    if (data && typeof data === "object") {
      const fieldErrors: Record<string, string> = {}
      for (const [key, val] of Object.entries(data)) {
        if (key === "detail") {
          setFormGlobalError(String(val))
        } else if (Array.isArray(val)) {
          fieldErrors[key] = val.join(" ")
        } else if (typeof val === "string") {
          fieldErrors[key] = val
        }
      }
      if (Object.keys(fieldErrors).length) setFormErrors(fieldErrors)
    } else {
      setFormGlobalError("An unexpected error occurred. Please try again.")
    }
  }

  function openCreateForm() {
    setEditingId(null)
    setForm({ ...EMPTY_FORM })
    setFormErrors({})
    setFormGlobalError(null)
    setFormOpen(true)
  }

  function openEditForm(customer: { id: string; name: string; company_name: string; email: string; phone: string; address: string; notes: string; status: string }) {
    setEditingId(customer.id)
    setForm({
      name: customer.name,
      company_name: customer.company_name,
      email: customer.email,
      phone: customer.phone,
      address: customer.address,
      notes: customer.notes,
      status: customer.status,
    })
    setFormErrors({})
    setFormGlobalError(null)
    setFormOpen(true)
  }

  function closeForm() {
    setFormOpen(false)
    setEditingId(null)
    setFormErrors({})
    setFormGlobalError(null)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormErrors({})
    setFormGlobalError(null)

    if (!form.name.trim()) {
      setFormErrors({ name: "Contact name is required." })
      return
    }

    if (editingId) {
      updateMutation.mutate({ id: editingId, payload: form })
    } else {
      createMutation.mutate(form)
    }
  }

  const data = customersQuery.data
  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1

  return (
    <div>
      <PageHeader
        title="Customers"
        description="Manage the companies and people you do business with."
        actions={<Button onClick={openCreateForm}>Add customer</Button>}
      />

      {customersQuery.isPending && <LoadingState label="Loading customers…" />}

      {customersQuery.isError && (
        <ErrorState
          title="Could not load customers"
          description="The server rejected or dropped the request. Check your connection and try again."
          onRetry={() => void customersQuery.refetch()}
        />
      )}

      {data && (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Input
              placeholder="Search by name, company, email, or phone…"
              value={search}
              onChange={handleSearchChange}
              className="sm:max-w-xs"
            />
            <Select value={statusFilter} onChange={handleStatusChange} className="sm:max-w-[160px]">
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </Select>
            {data.count > 0 && (
              <span className="ml-auto text-sm text-slate-500">
                {data.count} customer{data.count !== 1 ? "s" : ""}
              </span>
            )}
          </div>

          {data.results.length === 0 ? (
            <EmptyState
              title="No customers found"
              description={
                debouncedSearch || statusFilter
                  ? "Try adjusting your search or filters."
                  : "Add your first customer to get started."
              }
              action={
                !debouncedSearch && !statusFilter ? (
                  <Button onClick={openCreateForm}>Add customer</Button>
                ) : undefined
              }
            />
          ) : (
            <>
              <TableContainer>
                <Table>
                  <THead>
                    <TR>
                      <TH>Name</TH>
                      <TH className="hidden sm:table-cell">Company</TH>
                      <TH className="hidden md:table-cell">Email</TH>
                      <TH className="hidden lg:table-cell">Phone</TH>
                      <TH>Status</TH>
                      <TH className="hidden sm:table-cell">Created</TH>
                      <TH><span className="sr-only">Actions</span></TH>
                    </TR>
                  </THead>
                  <TBody>
                    {data.results.map((customer) => (
                      <TR key={customer.id}>
                        <TD>
                          <div>
                            <span className="font-medium text-slate-900">{customer.name}</span>
                            <span className="ml-0 block text-xs text-slate-500 sm:hidden">
                              {customer.company_name || "—"}
                            </span>
                          </div>
                        </TD>
                        <TD className="hidden sm:table-cell text-slate-600">
                          {customer.company_name || "—"}
                        </TD>
                        <TD className="hidden md:table-cell text-slate-600">
                          {customer.email || "—"}
                        </TD>
                        <TD className="hidden lg:table-cell text-slate-600">
                          {customer.phone || "—"}
                        </TD>
                        <TD><StatusBadge value={customer.status} /></TD>
                        <TD className="hidden sm:table-cell text-slate-500">
                          {formatDate(customer.created_at)}
                        </TD>
                        <TD>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openEditForm(customer)}
                            >
                              Edit
                            </Button>
                            {canDelete && customer.status !== "ARCHIVED" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  setArchiveTarget({ id: customer.id, name: customer.name })
                                }
                              >
                                Archive
                              </Button>
                            )}
                          </div>
                        </TD>
                      </TR>
                    ))}
                  </TBody>
                </Table>
              </TableContainer>

              {totalPages > 1 && (
                <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3">
                  <span className="text-sm text-slate-500">
                    Page {page} of {totalPages}
                  </span>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => p - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={page >= totalPages}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      <Modal
        open={formOpen}
        onClose={closeForm}
        title={editingId ? "Edit customer" : "Add customer"}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={closeForm}>Cancel</Button>
            <Button
              type="submit"
              form="customer-form"
              isLoading={createMutation.isPending || updateMutation.isPending}
            >
              {editingId ? "Save changes" : "Create customer"}
            </Button>
          </>
        }
      >
        <form id="customer-form" onSubmit={handleSubmit} className="space-y-4">
          {formGlobalError && (
            <div role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {formGlobalError}
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Contact name"
              placeholder="Jane Smith"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              error={formErrors.name}
              required
            />
            <Input
              label="Company name"
              placeholder="Acme Corp"
              value={form.company_name}
              onChange={(e) => setForm((f) => ({ ...f, company_name: e.target.value }))}
              error={formErrors.company_name}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Email"
              type="email"
              placeholder="jane@acme.com"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              error={formErrors.email}
            />
            <Input
              label="Phone"
              type="tel"
              placeholder="+1 (555) 123-4567"
              value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              error={formErrors.phone}
            />
          </div>

          <Input
            label="Address"
            placeholder="123 Main St, City, State 12345"
            value={form.address}
            onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
            error={formErrors.address}
          />

          <div>
            <label htmlFor="customer-notes" className="mb-1.5 block text-sm font-medium text-slate-700">
              Notes
            </label>
            <textarea
              id="customer-notes"
              rows={3}
              placeholder="Additional notes about this customer…"
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              className="block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
          </div>

          <Select
            label="Status"
            value={form.status}
            onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
            error={formErrors.status}
          >
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
            <option value="ARCHIVED">Archived</option>
          </Select>
        </form>
      </Modal>

      <Modal
        open={archiveTarget !== null}
        onClose={() => setArchiveTarget(null)}
        title="Archive customer"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setArchiveTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              isLoading={archiveMutation.isPending}
              onClick={() => archiveTarget && archiveMutation.mutate(archiveTarget.id)}
            >
              Archive
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          Are you sure you want to archive{" "}
          <span className="font-medium text-slate-900">{archiveTarget?.name}</span>?
        </p>
      </Modal>
    </div>
  )
}
