import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"

import { Button } from "@/components/ui/Button"
import { Card, CardContent, CardDescription, CardDivider, CardHeader, CardTitle } from "@/components/ui/Card"
import { ConfirmDialog } from "@/components/ui/ConfirmDialog"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { useAuth } from "@/hooks/useAuth"
import { useUnsavedChanges } from "@/hooks/useUnsavedChanges"
import { fetchWorkspace, updateWorkspace } from "@/features/company/api"
import { queryKeys } from "@/utils/queryKeys"

const COMPANY_LOCALES = [
  { value: "en", label: "English" },
  { value: "fr", label: "Français" },
  { value: "es", label: "Español" },
  { value: "ar", label: "العربية" },
  { value: "de", label: "Deutsch" },
] as const

const COMMON_TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/Sao_Paulo",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Europe/Moscow",
  "Asia/Dubai",
  "Asia/Kolkata",
  "Asia/Bangkok",
  "Asia/Shanghai",
  "Asia/Tokyo",
  "Australia/Sydney",
  "Pacific/Auckland",
] as const

export function WorkspacePage() {
  const { activeCompany, role } = useAuth()
  const isAdmin = role === "ADMIN"
  const queryClient = useQueryClient()

  const workspaceQuery = useQuery({
    queryKey: queryKeys.workspace(activeCompany?.id ?? null),
    queryFn: fetchWorkspace,
    enabled: activeCompany !== null,
  })

  const workspace = workspaceQuery.data

  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [timezone, setTimezone] = useState("UTC")
  const [locale, setLocale] = useState("en")
  const [logoFile, setLogoFile] = useState<File | null>(null)
  const [logoPreview, setLogoPreview] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (workspace) {
      setName(workspace.name)
      setDescription(workspace.description)
      setTimezone(workspace.timezone)
      setLocale(workspace.locale)
    }
  }, [workspace])

  const isDirty = useMemo(() => {
    if (!workspace) return false
    return (
      name !== workspace.name ||
      description !== workspace.description ||
      timezone !== workspace.timezone ||
      locale !== workspace.locale ||
      logoFile !== null
    )
  }, [workspace, name, description, timezone, locale, logoFile])

  const { showConfirm, handleConfirm, handleCancel } = useUnsavedChanges(isDirty)

  const handleLogoChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setLogoFile(file)
    setLogoPreview(URL.createObjectURL(file))
  }, [])

  const handleSave = useCallback(async () => {
    setSaving(true)
    setError(null)
    setSuccess(false)
    try {
      await updateWorkspace({ name, description, timezone, locale, logo: logoFile ?? undefined })
      await queryClient.invalidateQueries({ queryKey: queryKeys.workspace(activeCompany?.id ?? null) })
      setSuccess(true)
      setLogoFile(null)
    } catch {
      setError("Failed to save workspace settings.")
    } finally {
      setSaving(false)
    }
  }, [name, description, timezone, locale, logoFile, activeCompany, queryClient])

  if (workspaceQuery.isPending) {
    return <p className="text-sm text-slate-500">Loading workspace…</p>
  }
  if (workspaceQuery.isError || !workspace) {
    return <p className="text-sm text-red-600">Failed to load workspace settings.</p>
  }

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

      {!isAdmin && (
        <Card>
          <CardContent className="py-6">
            <p className="text-sm text-slate-600">
              Workspace settings can only be edited by an administrator.
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Workspace</CardTitle>
          <CardDescription>General settings for your workspace.</CardDescription>
        </CardHeader>
        <CardDivider />
        <CardContent>
          {isAdmin ? (
            <div className="space-y-4">
              <Input
                label="Workspace name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <div>
                <label htmlFor="ws-description" className="mb-1.5 block text-sm font-medium text-slate-700">
                  Description
                </label>
                <textarea
                  id="ws-description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm transition-colors focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 focus:outline-none"
                />
              </div>
              <Select
                label="Timezone"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
              >
                {COMMON_TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </Select>
              <Select
                label="Language"
                value={locale}
                onChange={(e) => setLocale(e.target.value)}
              >
                {COMPANY_LOCALES.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </Select>
            </div>
          ) : (
            <dl className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-slate-500">Name</dt>
                <dd className="mt-0.5 font-medium text-slate-900">{workspace.name}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Slug</dt>
                <dd className="mt-0.5 font-medium text-slate-900">{workspace.slug}</dd>
              </div>
              {workspace.description && (
                <div className="sm:col-span-2">
                  <dt className="text-slate-500">Description</dt>
                  <dd className="mt-0.5 font-medium text-slate-900">{workspace.description}</dd>
                </div>
              )}
              <div>
                <dt className="text-slate-500">Timezone</dt>
                <dd className="mt-0.5 font-medium text-slate-900">{workspace.timezone}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Language</dt>
                <dd className="mt-0.5 font-medium text-slate-900">
                  {COMPANY_LOCALES.find((l) => l.value === workspace.locale)?.label ?? workspace.locale}
                </dd>
              </div>
            </dl>
          )}
        </CardContent>
      </Card>

      {isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle>Logo</CardTitle>
            <CardDescription>Your workspace's visual identity.</CardDescription>
          </CardHeader>
          <CardDivider />
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="flex size-16 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
                {logoPreview ? (
                  <img src={logoPreview} alt="Logo preview" className="size-full object-contain" />
                ) : workspace.logo ? (
                  <img src={workspace.logo} alt="Workspace logo" className="size-full object-contain" />
                ) : (
                  <span className="text-lg font-medium text-slate-400">{workspace.name[0]}</span>
                )}
              </div>
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleLogoChange}
                />
                <Button variant="secondary" size="sm" onClick={() => fileInputRef.current?.click()}>
                  Upload logo
                </Button>
                {logoFile && (
                  <p className="mt-1.5 text-xs text-slate-500">{logoFile.name}</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {isAdmin && (
        <div className="space-y-3">
          {error && (
            <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
          )}
          {success && (
            <p role="status" className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
              Workspace updated successfully.
            </p>
          )}
          <div>
            <Button onClick={handleSave} isLoading={saving} disabled={!isDirty}>
              Save changes
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}