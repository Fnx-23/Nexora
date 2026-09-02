import { useCallback, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { PageHeader } from "@/components/layout/PageHeader"
import { ChevronDownIcon } from "@/components/icons"
import { Avatar } from "@/components/ui/Avatar"
import { StatusBadge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { Dropdown, DropdownItem, DropdownSeparator } from "@/components/ui/Dropdown"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { Modal } from "@/components/ui/Modal"
import { ErrorState } from "@/components/ui/ErrorState"
import { EmptyState } from "@/components/ui/EmptyState"
import { LoadingState } from "@/components/ui/LoadingState"
import { Card } from "@/components/ui/Card"
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
  changeMemberRole,
  createInvitation,
  deactivateMember,
  fetchInvitations,
  fetchMembers,
  reactivateMember,
  removeMember,
  resendInvitation,
  revokeInvitation,
} from "@/features/team/api"
import type { Invitation, Member } from "@/types/team"
import type { Role } from "@/types/auth"
import { queryKeys } from "@/utils/queryKeys"

const ROLE_OPTIONS: { value: Role; label: string }[] = [
  { value: "ADMIN", label: "Admin" },
  { value: "MANAGER", label: "Manager" },
  { value: "EMPLOYEE", label: "Employee" },
]

function formatDate(iso: string | null) {
  if (!iso) return "—"
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

export function TeamPage() {
  const { activeCompany, role, user } = useAuth()
  const queryClient = useQueryClient()
  const companyId = activeCompany?.id ?? null

  const isAdmin = role === "ADMIN"
  const canInvite = isAdmin || role === "MANAGER"

  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviteEmail, setInviteEmail] = useState("")
  const [inviteRole, setInviteRole] = useState<Role>("EMPLOYEE")
  const [inviteErrors, setInviteErrors] = useState<Record<string, string>>({})
  const [actionError, setActionError] = useState<string | null>(null)
  const [confirmTarget, setConfirmTarget] = useState<{
    kind: "deactivate" | "remove"
    membershipId: string
    name: string
  } | null>(null)
  const [revokeTarget, setRevokeTarget] = useState<Invitation | null>(null)

  const membersQuery = useQuery({
    queryKey: queryKeys.members(companyId),
    queryFn: fetchMembers,
    enabled: companyId !== null,
  })

  const invitationsQuery = useQuery({
    queryKey: queryKeys.invitations(companyId),
    queryFn: fetchInvitations,
    enabled: companyId !== null && canInvite,
  })

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.members(companyId) })
    if (canInvite) {
      void queryClient.invalidateQueries({ queryKey: queryKeys.invitations(companyId) })
    }
  }, [queryClient, companyId, canInvite])

  const createInviteMutation = useMutation({
    mutationFn: createInvitation,
    onSuccess: () => {
      setInviteOpen(false)
      setInviteEmail("")
      setInviteRole("EMPLOYEE")
      setInviteErrors({})
      invalidate()
    },
    onError: (err: Error & { response?: { data?: Record<string, unknown> } }) => {
      const data = err.response?.data
      if (data && typeof data === "object") {
        const fieldErrors: Record<string, string> = {}
        for (const [key, val] of Object.entries(data)) {
          if (key === "detail") {
            setInviteErrors({ email: String(val) })
          } else if (typeof val === "string") {
            fieldErrors[key] = val
          }
        }
        if (Object.keys(fieldErrors).length) setInviteErrors(fieldErrors)
      }
    },
  })

  const revokeMutation = useMutation({
    mutationFn: revokeInvitation,
    onSuccess: () => {
      setRevokeTarget(null)
      invalidate()
    },
    onError: () => setActionError("Could not revoke the invitation. Please try again."),
  })

  const resendMutation = useMutation({
    mutationFn: resendInvitation,
    onError: () => setActionError("Could not resend the invitation. Please try again."),
    onSuccess: () => invalidate(),
  })

  const roleMutation = useMutation({
    mutationFn: ({ id, role: newRole }: { id: string; role: Role }) =>
      changeMemberRole(id, newRole),
    onError: (err: Error & { response?: { data?: { detail?: string } } }) =>
      setActionError(err.response?.data?.detail ?? "Could not update the role."),
    onSuccess: () => invalidate(),
  })

  const statusMutation = useMutation({
    mutationFn: (membershipId: string) =>
      confirmTarget?.kind === "deactivate"
        ? deactivateMember(membershipId)
        : reactivateMember(membershipId),
    onSuccess: () => {
      setConfirmTarget(null)
      invalidate()
    },
    onError: () => setActionError("Could not update the member. Please try again."),
  })

  const removeMutation = useMutation({
    mutationFn: removeMember,
    onSuccess: () => {
      setConfirmTarget(null)
      invalidate()
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      setConfirmTarget(null)
      setActionError(err.response?.data?.detail ?? "Could not remove the member.")
    },
  })

  const handleInviteSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setInviteErrors({})
    if (!inviteEmail.trim()) {
      setInviteErrors({ email: "An email address is required." })
      return
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inviteEmail.trim())) {
      setInviteErrors({ email: "Enter a valid email address." })
      return
    }
    createInviteMutation.mutate({ email: inviteEmail.trim(), role: inviteRole })
  }

  const members = membersQuery.data ?? []
  const invitations = invitationsQuery.data ?? []

  return (
    <div>
      <PageHeader
        title="Team"
        description="Everyone with access to this workspace, plus pending invitations."
        actions={
          canInvite ? (
            <Button onClick={() => setInviteOpen(true)}>Invite member</Button>
          ) : undefined
        }
      />

      {actionError && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {actionError}
          <button
            type="button"
            className="ml-2 font-medium underline-offset-2 hover:underline"
            onClick={() => setActionError(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      {membersQuery.isPending && <LoadingState label="Loading team members…" />}

      {membersQuery.isError && (
        <ErrorState
          title="Could not load your team"
          description="The server rejected or dropped the request. Check your connection and try again."
          onRetry={() => void membersQuery.refetch()}
        />
      )}

      {membersQuery.data && (
        <div className="space-y-8">
          <section aria-labelledby="members-heading">
            <h2 id="members-heading" className="mb-3 text-sm font-semibold text-slate-900">
              Members <span className="font-normal text-slate-400">({members.length})</span>
            </h2>
            {members.length === 0 ? (
              <EmptyState
                title="No members yet"
                description="Invite colleagues to this workspace to start collaborating."
                action={
                  canInvite ? (
                    <Button onClick={() => setInviteOpen(true)}>Invite member</Button>
                  ) : undefined
                }
              />
            ) : (
              <Card className="overflow-hidden">
                <TableContainer>
                  <Table>
                    <THead>
                      <TR>
                        <TH>Name</TH>
                        <TH>Email</TH>
                        <TH>Role</TH>
                        <TH className="hidden md:table-cell">Joined</TH>
                        <TH>Status</TH>
                        {isAdmin && (
                          <TH>
                            <span className="sr-only">Actions</span>
                          </TH>
                        )}
                      </TR>
                    </THead>
                    <TBody>
                      {members.map((member) => {
                        const isSelf = member.id === user?.id
                        return (
                          <TR key={member.id}>
                            <TD>
                              <div className="flex items-center gap-3">
                                <Avatar name={member.full_name || member.email} size="sm" />
                                <div>
                                  <span className="font-medium text-slate-900">
                                    {member.full_name || "—"}
                                  </span>
                                  {isSelf && (
                                    <span className="ml-2 rounded bg-brand-50 px-1.5 py-0.5 text-xs font-medium text-brand-700">
                                      You
                                    </span>
                                  )}
                                </div>
                              </div>
                            </TD>
                            <TD className="text-slate-600">{member.email}</TD>
                            <TD>
                              {isAdmin && !isSelf ? (
                                <RoleDropdown
                                  value={member.role}
                                  onSelect={(newRole) =>
                                    roleMutation.mutate({
                                      id: member.membership_id,
                                      role: newRole,
                                    })
                                  }
                                />
                              ) : member.role ? (
                                <StatusBadge value={member.role} />
                              ) : (
                                "—"
                              )}
                            </TD>
                            <TD className="hidden text-slate-500 md:table-cell">
                              {formatDate(member.joined_at)}
                            </TD>
                            <TD>
                              {member.membership_active ? (
                                <StatusBadge value="ACTIVE" />
                              ) : (
                                <StatusBadge value="INACTIVE" />
                              )}
                            </TD>
                            {isAdmin && (
                              <TD>
                                <MemberActions
                                  member={member}
                                  isSelf={isSelf}
                                  onDeactivate={() =>
                                    setConfirmTarget({
                                      kind: "deactivate",
                                      membershipId: member.membership_id,
                                      name: member.full_name || member.email,
                                    })
                                  }
                                  onReactivate={() =>
                                    statusMutation.mutate(member.membership_id)
                                  }
                                  onRemove={() =>
                                    setConfirmTarget({
                                      kind: "remove",
                                      membershipId: member.membership_id,
                                      name: member.full_name || member.email,
                                    })
                                  }
                                />
                              </TD>
                            )}
                          </TR>
                        )
                      })}
                    </TBody>
                  </Table>
                </TableContainer>
              </Card>
            )}
          </section>

          {canInvite && (
            <section aria-labelledby="invitations-heading">
              <h2 id="invitations-heading" className="mb-3 text-sm font-semibold text-slate-900">
                Pending invitations <span className="font-normal text-slate-400">({invitations.length})</span>
              </h2>
              {invitations.length === 0 ? (
                <EmptyState
                  title="No pending invitations"
                  description="People you invite will appear here until they accept."
                />
              ) : (
                <Card className="overflow-hidden">
                  <TableContainer>
                    <Table>
                      <THead>
                        <TR>
                          <TH>Email</TH>
                          <TH>Role</TH>
                          <TH className="hidden sm:table-cell">Invited by</TH>
                          <TH className="hidden md:table-cell">Expires</TH>
                          <TH>
                            <span className="sr-only">Actions</span>
                          </TH>
                        </TR>
                      </THead>
                      <TBody>
                        {invitations.map((invitation) => (
                          <TR key={invitation.id}>
                            <TD className="font-medium text-slate-900">{invitation.email}</TD>
                            <TD>
                              {invitation.role ? (
                                <StatusBadge value={invitation.role} />
                              ) : (
                                "—"
                              )}
                            </TD>
                            <TD className="hidden text-slate-600 sm:table-cell">
                              {invitation.invited_by_name || "—"}
                            </TD>
                            <TD className="hidden text-slate-500 md:table-cell">
                              {formatDate(invitation.expires_at)}
                            </TD>
                            <TD>
                              <div className="flex items-center gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  isLoading={resendMutation.isPending}
                                  onClick={() => resendMutation.mutate(invitation.id)}
                                >
                                  Resend
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="text-red-600 hover:bg-red-50"
                                  onClick={() => setRevokeTarget(invitation)}
                                >
                                  Revoke
                                </Button>
                              </div>
                            </TD>
                          </TR>
                        ))}
                      </TBody>
                    </Table>
                  </TableContainer>
                </Card>
              )}
            </section>
          )}
        </div>
      )}

      <Modal
        open={inviteOpen}
        onClose={() => setInviteOpen(false)}
        title="Invite a team member"
        description="They'll receive an email with a link to join this workspace."
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setInviteOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              form="invite-form"
              isLoading={createInviteMutation.isPending}
            >
              Send invitation
            </Button>
          </>
        }
      >
        <form id="invite-form" onSubmit={handleInviteSubmit} className="space-y-4">
          <Input
            label="Email address"
            type="email"
            placeholder="colleague@company.com"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            error={inviteErrors.email}
            autoFocus
          />
          <Select
            label="Role"
            value={inviteRole}
            onChange={(e) => setInviteRole(e.target.value as Role)}
          >
            {ROLE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
        </form>
      </Modal>

      <Modal
        open={revokeTarget !== null}
        onClose={() => setRevokeTarget(null)}
        title="Revoke invitation"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setRevokeTarget(null)}>
              Keep
            </Button>
            <Button
              variant="danger"
              isLoading={revokeMutation.isPending}
              onClick={() => revokeTarget && revokeMutation.mutate(revokeTarget.id)}
            >
              Revoke
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          Revoke the invitation sent to{" "}
          <span className="font-medium text-slate-900">{revokeTarget?.email}</span>? They won't be
          able to join with this link anymore.
        </p>
      </Modal>

      <Modal
        open={confirmTarget !== null}
        onClose={() => setConfirmTarget(null)}
        title={confirmTarget?.kind === "deactivate" ? "Deactivate member" : "Remove member"}
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setConfirmTarget(null)}>
              Cancel
            </Button>
            {confirmTarget?.kind === "deactivate" ? (
              <Button
                variant="danger"
                isLoading={statusMutation.isPending}
                onClick={() => confirmTarget && statusMutation.mutate(confirmTarget.membershipId)}
              >
                Deactivate
              </Button>
            ) : (
              <Button
                variant="danger"
                isLoading={removeMutation.isPending}
                onClick={() =>
                  confirmTarget && removeMutation.mutate(confirmTarget.membershipId)
                }
              >
                Remove
              </Button>
            )}
          </>
        }
      >
        {confirmTarget?.kind === "deactivate" ? (
          <p className="text-sm text-slate-600">
            Deactivate <span className="font-medium text-slate-900">{confirmTarget.name}</span>?
            They'll lose access until an admin reactivates them.
          </p>
        ) : (
          <p className="text-sm text-slate-600">
            Remove <span className="font-medium text-slate-900">{confirmTarget?.name}</span> from
            this workspace permanently?
          </p>
        )}
      </Modal>
    </div>
  )
}

function RoleDropdown({
  value,
  onSelect,
}: {
  value: Role | ""
  onSelect: (role: Role) => void
}) {
  const current = ROLE_OPTIONS.find((opt) => opt.value === value)
  return (
    <Dropdown
      trigger={({ toggle, triggerProps }) => (
        <button
          type="button"
          {...triggerProps}
          onClick={toggle}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-2 py-1 text-xs font-medium text-slate-700 transition-colors hover:border-slate-300 hover:bg-slate-50"
        >
          {current?.label ?? "—"}
          <ChevronDownIcon className="size-3.5 text-slate-400" />
        </button>
      )}
    >
      {ROLE_OPTIONS.map((opt) => (
        <DropdownItem
          key={opt.value}
          onClick={() => {
            if (opt.value !== value) onSelect(opt.value)
          }}
        >
          {opt.label}
        </DropdownItem>
      ))}
    </Dropdown>
  )
}

function MemberActions({
  member,
  isSelf,
  onDeactivate,
  onReactivate,
  onRemove,
}: {
  member: Member
  isSelf: boolean
  onDeactivate: () => void
  onReactivate: () => void
  onRemove: () => void
}) {
  return (
    <Dropdown
      trigger={({ toggle, triggerProps }) => (
        <button
          type="button"
          {...triggerProps}
          onClick={toggle}
          className="rounded-lg px-2.5 py-1.5 text-sm font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
        >
          Actions
        </button>
      )}
    >
      {member.membership_active ? (
        <DropdownItem disabled={isSelf} onClick={onDeactivate}>
          Deactivate
        </DropdownItem>
      ) : (
        <DropdownItem onClick={onReactivate}>Reactivate</DropdownItem>
      )}
      <DropdownSeparator />
      <DropdownItem danger disabled={isSelf} onClick={onRemove}>
        Remove
      </DropdownItem>
    </Dropdown>
  )
}
