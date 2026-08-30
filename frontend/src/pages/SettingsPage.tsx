import { useCallback, useRef, useState } from "react"

import { PageHeader } from "@/components/layout/PageHeader"
import {
  Card,
  CardContent,
  CardDescription,
  CardDivider,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card"
import { StatusBadge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { useAuth } from "@/hooks/useAuth"
import { api } from "@/services/api"

export function SettingsPage() {
  const { user, activeCompany, role, refreshSession } = useAuth()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [uploadSuccess, setUploadSuccess] = useState(false)

  const handleAvatarUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) return

      setUploading(true)
      setUploadError(null)
      setUploadSuccess(false)

      try {
        const formData = new FormData()
        formData.append("avatar", file)
        await api.patch("/auth/me/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        })
        await refreshSession()
        setUploadSuccess(true)
      } catch {
        setUploadError("Upload failed. Please try a different image.")
      } finally {
        setUploading(false)
        if (fileInputRef.current) fileInputRef.current.value = ""
      }
    },
    [refreshSession],
  )

  return (
    <div>
      <PageHeader title="Settings" description="Company and account configuration." />

      <div className="max-w-3xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Company</CardTitle>
            <CardDescription>
              Details of the workspace you are currently signed into.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-x-8 gap-y-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-slate-500">Name</dt>
                <dd className="mt-0.5 font-medium text-slate-900">{activeCompany?.name ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Slug</dt>
                <dd className="mt-0.5 font-medium text-slate-900">{activeCompany?.slug ?? "—"}</dd>
              </div>
            </dl>
            <p className="mt-4 text-xs text-slate-400">
              Editing company details requires the ADMIN role (PATCH /api/v1/companies/current/).
            </p>
          </CardContent>
          <CardDivider />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Your profile</CardTitle>
            <CardDescription>How you appear to the rest of your company.</CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-x-8 gap-y-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-slate-500">Full name</dt>
                <dd className="mt-0.5 font-medium text-slate-900">
                  {user?.full_name || "—"}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Email</dt>
                <dd className="mt-0.5 font-medium text-slate-900">{user?.email ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Role</dt>
                <dd className="mt-0.5">{role ? <StatusBadge value={role} /> : "—"}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Roles &amp; permissions</CardTitle>
            <CardDescription>Reference for the built-in roles.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-slate-600">
            <p>
              <span className="font-medium text-slate-900">Admins</span> manage company settings,
              members and billing.
            </p>
            <p>
              <span className="font-medium text-slate-900">Managers</span> run projects, tasks and
              customer relationships.
            </p>
            <p>
              <span className="font-medium text-slate-900">Employees</span> work on assigned
              projects and tasks.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Avatar</CardTitle>
            <CardDescription>Your profile picture visible to team members.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 shrink-0 rounded-full bg-slate-100 flex items-center justify-center overflow-hidden">
                {user?.avatar ? (
                  <img
                    src={user.avatar}
                    alt={user.full_name}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="text-xl font-medium text-slate-500">
                    {user?.first_name?.[0]}
                    {user?.last_name?.[0]}
                  </span>
                )}
              </div>
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleAvatarUpload}
                />
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={uploading}
                  onClick={() => fileInputRef.current?.click()}
                >
                  {uploading ? "Uploading…" : "Change avatar"}
                </Button>
                {uploadError && (
                  <p className="mt-1 text-xs text-red-600">{uploadError}</p>
                )}
                {uploadSuccess && (
                  <p className="mt-1 text-xs text-green-600">Avatar updated.</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
