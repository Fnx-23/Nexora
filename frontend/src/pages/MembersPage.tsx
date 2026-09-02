import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"

import { Button } from "@/components/ui/Button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card"
import { StatusBadge } from "@/components/ui/Badge"
import { useAuth } from "@/hooks/useAuth"
import { fetchMembers } from "@/features/team/api"
import { queryKeys } from "@/utils/queryKeys"

export function MembersPage() {
  const { activeCompany } = useAuth()
  const navigate = useNavigate()

  const { data: members } = useQuery({
    queryKey: queryKeys.members(activeCompany?.id ?? null),
    queryFn: fetchMembers,
    enabled: activeCompany !== null,
  })

  const totalMembers = members?.length ?? 0
  const admins = members?.filter((m) => m.role === "ADMIN").length ?? 0
  const managers = members?.filter((m) => m.role === "MANAGER").length ?? 0
  const employees = members?.filter((m) => m.role === "EMPLOYEE").length ?? 0

  return (
    <div className="space-y-4 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Members</CardTitle>
          <CardDescription>
            Summary of who belongs to {activeCompany?.name ?? "your workspace"}.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-x-8 gap-y-4 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-slate-500">Total members</dt>
              <dd className="mt-0.5 font-semibold text-slate-900">{totalMembers}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Admins</dt>
              <dd className="mt-0.5">{admins > 0 ? <StatusBadge value="ADMIN" /> : "0"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Managers</dt>
              <dd className="mt-0.5">{managers > 0 ? <StatusBadge value="MANAGER" /> : "0"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Employees</dt>
              <dd className="mt-0.5">{employees > 0 ? <StatusBadge value="EMPLOYEE" /> : "0"}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <div>
        <Button variant="secondary" onClick={() => navigate("/team")}>
          Go to Team Management
        </Button>
        <p className="mt-2 text-xs text-slate-400">
          Manage roles, invitations, and deactivations on the Team page.
        </p>
      </div>
    </div>
  )
}