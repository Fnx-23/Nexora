import { useQuery } from "@tanstack/react-query"

import { PageHeader } from "@/components/layout/PageHeader"
import { Avatar } from "@/components/ui/Avatar"
import { StatusBadge } from "@/components/ui/Badge"
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
import { fetchMembers } from "@/features/team/api"
import { queryKeys } from "@/utils/queryKeys"

export function TeamPage() {
  const { activeCompany } = useAuth()
  const membersQuery = useQuery({
    queryKey: queryKeys.members(activeCompany?.id ?? null),
    queryFn: fetchMembers,
  })

  return (
    <div>
      <PageHeader
        title="Team"
        description="Everyone with access to this workspace."
      />

      {membersQuery.isPending && <LoadingState label="Loading team members…" />}

      {membersQuery.isError && (
        <ErrorState
          title="Could not load your team"
          description="The server rejected or dropped the request. Check your connection and try again."
          onRetry={() => void membersQuery.refetch()}
        />
      )}

      {membersQuery.data && (
        membersQuery.data.length === 0 ? (
          <EmptyState title="No members yet" description="Invite colleagues once invitations ship." />
        ) : (
          <TableContainer>
            <Table>
              <THead>
                <TR>
                  <TH>Name</TH>
                  <TH>Email</TH>
                  <TH>Role</TH>
                </TR>
              </THead>
              <TBody>
                {membersQuery.data.map((member) => (
                  <TR key={member.id}>
                    <TD>
                      <div className="flex items-center gap-3">
                        <Avatar name={member.full_name || member.email} size="sm" />
                        <span className="font-medium text-slate-900">
                          {member.full_name || "—"}
                        </span>
                      </div>
                    </TD>
                    <TD className="text-slate-600">{member.email}</TD>
                    <TD>{member.role ? <StatusBadge value={member.role} /> : "—"}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          </TableContainer>
        )
      )}
    </div>
  )
}
