import { useCallback, useState } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"

import { Button } from "@/components/ui/Button"
import { Card, CardContent, CardDescription, CardDivider, CardHeader, CardTitle } from "@/components/ui/Card"
import { Input } from "@/components/ui/Input"
import { StatusBadge } from "@/components/ui/Badge"
import { ConfirmDialog } from "@/components/ui/ConfirmDialog"
import { TableContainer, Table, THead, TBody, TR, TH, TD } from "@/components/ui/Table"
import { useAuth } from "@/hooks/useAuth"
import {
  changePassword,
  fetchSessions,
  fetchSecurityEvents,
  revokeAllOtherSessions,
  revokeSession,
  verifyEmail,
} from "@/features/auth/securityApi"
import type { SecurityEvent, SessionDeviceInfo } from "@/features/auth/securityTypes"
import { queryKeys } from "@/utils/queryKeys"

const SESSION_KEYS = ["sessions"] as const

const SECURITY_EVENT_LABELS: Record<string, string> = {
  login: "Logged in",
  login_failed: "Failed login attempt",
  password_changed: "Password changed",
  password_reset: "Password reset",
  email_verified: "Email verified",
  profile_updated: "Profile updated",
  session_revoked: "Session revoked",
  sessions_revoked_others: "All other sessions revoked",
}

export function SecurityPage() {
  return (
    <div className="space-y-6">
      <PasswordChangeSection />
      <SessionsSection />
      <SecurityActivitySection />
    </div>
  )
}

function PasswordChangeSection() {
  const { refreshSession } = useAuth()
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const mutation = useMutation({
    mutationFn: changePassword,
    onSuccess: () => {
      setSuccess(true)
      setError(null)
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
      void refreshSession()
    },
    onError: (err: { response?: { data?: { detail?: string; current_password?: string[]; new_password?: string[] } } }) => {
      const data = err?.response?.data
      if (data?.detail) {
        setError(data.detail)
      } else if (data?.current_password) {
        setError(data.current_password[0])
      } else if (data?.new_password) {
        setError(data.new_password[0])
      } else {
        setError("Failed to change password. Please check your current password.")
      }
    },
  })

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      setError(null)
      setSuccess(false)
      if (newPassword !== confirmPassword) {
        setError("New passwords do not match.")
        return
      }
      mutation.mutate({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      })
    },
    [currentPassword, newPassword, confirmPassword, mutation],
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle>Change Password</CardTitle>
        <CardDescription>Update your password to keep your account secure.</CardDescription>
      </CardHeader>
      <CardDivider />
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
          <Input
            label="Current password"
            type="password"
            name="current_password"
            autoComplete="current-password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
          <Input
            label="New password"
            type="password"
            name="new_password"
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
          <Input
            label="Confirm new password"
            type="password"
            name="confirm_password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
          {error && (
            <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}
          {success && (
            <p role="status" className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
              Password changed successfully.
            </p>
          )}
          <Button type="submit" isLoading={mutation.isPending} disabled={mutation.isPending}>
            Change Password
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

function SessionsSection() {
  const { refreshSession, user } = useAuth()
  const [revokeLoading, setRevokeLoading] = useState<string | null>(null)
  const [revokeAllLoading, setRevokeAllLoading] = useState(false)
  const [showRevokeAllConfirm, setShowRevokeAllConfirm] = useState(false)
  const [verifyLoading, setVerifyLoading] = useState(false)
  const [verifySuccess, setVerifySuccess] = useState(false)
  const [verifyError, setVerifyError] = useState<string | null>(null)

  const { data, isPending, isError } = useQuery({
    queryKey: [...SESSION_KEYS],
    queryFn: fetchSessions,
  })

  const handleRevoke = useCallback(
    async (sessionId: string) => {
      if (revokeLoading) return
      setRevokeLoading(sessionId)
      try {
        await revokeSession(sessionId)
        await refreshSession()
      } catch (err) {
        void err
      } finally {
        setRevokeLoading(null)
      }
    },
    [revokeLoading, refreshSession],
  )

  const handleRevokeAll = useCallback(async () => {
    if (revokeAllLoading) return
    setRevokeAllLoading(true)
    try {
      await revokeAllOtherSessions()
      await refreshSession()
      setShowRevokeAllConfirm(false)
    } catch (err) {
      void err
    } finally {
      setRevokeAllLoading(false)
    }
  }, [revokeAllLoading, refreshSession])

  const handleVerify = useCallback(async () => {
    if (!user || user.is_email_verified || verifyLoading) return
    setVerifyLoading(true)
    setVerifyError(null)
    setVerifySuccess(false)
    try {
      await verifyEmail()
      setVerifySuccess(true)
      await refreshSession()
    } catch {
      setVerifyError("Failed to verify email. Please try again.")
    } finally {
      setVerifyLoading(false)
    }
  }, [user, verifyLoading, refreshSession])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Security & Sessions</CardTitle>
        <CardDescription>
          Manage your password, verify your email, and review active sessions.
        </CardDescription>
      </CardHeader>
      <CardDivider />
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-900">Email Verification</p>
            <p className="text-sm text-slate-500">
              {user?.is_email_verified ? "Your email is verified." : "Verify your email to unlock all features."}
            </p>
          </div>
          {!user?.is_email_verified && (
            <Button variant="secondary" size="sm" onClick={handleVerify} isLoading={verifyLoading}>
              {verifyLoading ? "Verifying…" : "Verify Email"}
            </Button>
          )}
        </div>
        {verifySuccess && (
          <p className="text-xs text-emerald-600">Email verified successfully!</p>
        )}
        {verifyError && (
          <p className="text-xs text-red-600">{verifyError}</p>
        )}

        <div>
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-slate-900">Active Sessions</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowRevokeAllConfirm(true)}
              isLoading={revokeAllLoading}
            >
              Logout All Others
            </Button>
          </div>

          {isPending && <p className="text-sm text-slate-500">Loading sessions…</p>}
          {isError && <p className="text-sm text-red-600">Failed to load sessions.</p>}
          {data && data.results.length === 0 && (
            <p className="text-sm text-slate-500">No active sessions.</p>
          )}
          {data && data.results.length > 0 && (
            <TableContainer>
              <Table>
                <THead>
                  <TR>
                    <TH>Device</TH>
                    <TH>IP Address</TH>
                    <TH>Last Active</TH>
                    <TH></TH>
                  </TR>
                </THead>
                <TBody>
                  {data.results.map((session: SessionDeviceInfo) => (
                    <TR key={session.id}>
                      <TD className="flex items-center gap-2">
                        <span>{session.browser}</span>
                        <span className="text-slate-400">·</span>
                        <span>{session.device}</span>
                        {session.is_current && <StatusBadge value="ACTIVE" />}
                      </TD>
                      <TD className="font-mono text-xs">{session.ip_address || "—"}</TD>
                      <TD>{new Date(session.last_activity).toLocaleString()}</TD>
                      <TD>
                        {!session.is_current && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => void handleRevoke(session.id)}
                            isLoading={revokeLoading === session.id}
                          >
                            Revoke
                          </Button>
                        )}
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            </TableContainer>
          )}
        </div>
      </CardContent>

      <ConfirmDialog
        open={showRevokeAllConfirm}
        onConfirm={() => void handleRevokeAll()}
        onCancel={() => setShowRevokeAllConfirm(false)}
        title="Logout all other sessions?"
        description="This will immediately sign out all other active sessions. The current session will remain active."
        confirmLabel="Logout all others"
        isLoading={revokeAllLoading}
      />
    </Card>
  )
}

function SecurityActivitySection() {
  const { data } = useQuery({
    queryKey: queryKeys.securityEvents(),
    queryFn: fetchSecurityEvents,
  })

  const events = data?.results ?? []

  return (
    <Card>
      <CardHeader>
        <CardTitle>Security Activity</CardTitle>
        <CardDescription>Recent security events on your account.</CardDescription>
      </CardHeader>
      <CardDivider />
      <CardContent>
        {events.length === 0 ? (
          <p className="text-sm text-slate-500">No security activity recorded yet.</p>
        ) : (
          <TableContainer>
            <Table>
              <THead>
                <TR>
                  <TH>Event</TH>
                  <TH>IP Address</TH>
                  <TH>Date</TH>
                </TR>
              </THead>
              <TBody>
                {events.map((event: SecurityEvent) => (
                  <TR key={event.id}>
                    <TD className="text-sm font-medium text-slate-900">
                      {SECURITY_EVENT_LABELS[event.event_type] ?? event.event_type}
                    </TD>
                    <TD className="font-mono text-xs text-slate-500">{event.ip_address || "—"}</TD>
                    <TD className="text-sm text-slate-500">
                      {new Date(event.created_at).toLocaleString()}
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          </TableContainer>
        )}
      </CardContent>
    </Card>
  )
}