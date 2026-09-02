import { useCallback, useRef, useState } from "react"

import { Button } from "@/components/ui/Button"
import { Card, CardContent, CardDescription, CardDivider, CardHeader, CardTitle } from "@/components/ui/Card"
import { ConfirmDialog } from "@/components/ui/ConfirmDialog"
import { Input } from "@/components/ui/Input"
import { Avatar } from "@/components/ui/Avatar"
import { useAuth } from "@/hooks/useAuth"
import { useUnsavedChanges } from "@/hooks/useUnsavedChanges"
import { api } from "@/services/api"

export function AccountPage() {
  const { user, refreshSession } = useAuth()
  const [firstName, setFirstName] = useState(user?.first_name ?? "")
  const [lastName, setLastName] = useState(user?.last_name ?? "")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const isDirty = firstName !== (user?.first_name ?? "") || lastName !== (user?.last_name ?? "")
  const { showConfirm, handleConfirm, handleCancel } = useUnsavedChanges(isDirty)

  const handleSave = useCallback(async () => {
    setSaving(true)
    setError(null)
    setSuccess(false)
    try {
      await api.patch("/auth/me/", { first_name: firstName, last_name: lastName })
      await refreshSession()
      setSuccess(true)
    } catch {
      setError("Failed to update profile. Please try again.")
    } finally {
      setSaving(false)
    }
  }, [firstName, lastName, refreshSession])

  return (
    <div className="space-y-4 max-w-2xl">
      <ConfirmDialog
        open={showConfirm}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
        title="Unsaved changes"
        description="You have unsaved changes that will be lost if you leave this page."
        confirmLabel="Leave"
        cancelLabel="Stay"
        variant="danger"
      />

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>
            Your personal information as it appears to other team members.
          </CardDescription>
        </CardHeader>
        <CardDivider />
        <CardContent>
          <dl className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-slate-500">First name</dt>
              <dd className="mt-0.5 font-medium text-slate-900">{user?.first_name || "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Last name</dt>
              <dd className="mt-0.5 font-medium text-slate-900">{user?.last_name || "—"}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-slate-500">Email</dt>
              <dd className="mt-0.5 font-medium text-slate-900">{user?.email ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Account created</dt>
              <dd className="mt-0.5 font-medium text-slate-900">
                {user ? new Date(user.created_at || Date.now()).toLocaleDateString() : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Email verified</dt>
              <dd className="mt-0.5">
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${user?.is_email_verified ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                  {user?.is_email_verified ? "Verified" : "Not verified"}
                </span>
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <AvatarUploadCard />

      <Card>
        <CardHeader>
          <CardTitle>Edit name</CardTitle>
          <CardDescription>Update your first and last name.</CardDescription>
        </CardHeader>
        <CardDivider />
        <CardContent>
          <div className="flex gap-4">
            <Input
              label="First name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="flex-1"
            />
            <Input
              label="Last name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              className="flex-1"
            />
          </div>
          {error && (
            <p role="alert" className="mt-3 text-sm text-red-700">
              {error}
            </p>
          )}
          {success && (
            <p role="status" className="mt-3 text-sm text-emerald-700">
              Profile updated successfully.
            </p>
          )}
          <div className="mt-4">
            <Button onClick={handleSave} isLoading={saving} disabled={!isDirty}>
              Save changes
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function AvatarUploadCard() {
  const { user, refreshSession } = useAuth()
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
    <Card>
      <CardHeader>
        <CardTitle>Avatar</CardTitle>
        <CardDescription>Your profile picture visible to team members.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <Avatar
            name={user?.full_name ?? "User"}
            src={user?.avatar}
            size="lg"
          />
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
              <p className="mt-1.5 text-xs text-red-600">{uploadError}</p>
            )}
            {uploadSuccess && (
              <p className="mt-1.5 text-xs text-emerald-600">Avatar updated.</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}