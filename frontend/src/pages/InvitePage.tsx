import { useState } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Navigate, useNavigate, useParams } from "react-router-dom"

import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { LoadingState } from "@/components/ui/LoadingState"
import { NexoraLogo } from "@/components/NexoraLogo"
import { useAuth } from "@/hooks/useAuth"
import { tokenStorage } from "@/services/tokenStorage"
import {
  acceptInvitation,
  registerAndAcceptInvitation,
  validateInvitation,
} from "@/features/team/api"

export function InvitePage() {
  const { token = "" } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const { status, user, refreshSession } = useAuth()

  const [first_name, setFirstName] = useState("")
  const [last_name, setLastName] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)

  const validationQuery = useQuery({
    queryKey: ["invitation", token],
    queryFn: () => validateInvitation(token),
    enabled: token.length > 0,
    retry: false,
  })

  const registerMutation = useMutation({
    mutationFn: () =>
      registerAndAcceptInvitation({
        token,
        email: validationQuery.data?.email ?? "",
        first_name: first_name.trim(),
        last_name: last_name.trim(),
        password,
      }),
    onSuccess: async (data) => {
      tokenStorage.save(data.tokens.access, data.tokens.refresh)
      await refreshSession()
      navigate("/dashboard", { replace: true })
    },
    onError: (err: { response?: { data?: Record<string, unknown> } }) => {
      const data = err.response?.data
      const fieldErrors: Record<string, string> = {}
      if (data && typeof data === "object") {
        for (const [key, val] of Object.entries(data)) {
          if (key === "detail") setFormError(String(val))
          else if (Array.isArray(val)) fieldErrors[key] = val.join(" ")
          else if (typeof val === "string") fieldErrors[key] = val
        }
      }
      if (Object.keys(fieldErrors).length) setFormErrors(fieldErrors)
      else setFormError((f) => f ?? "Could not complete your registration. Please try again.")
    },
  })

  const acceptMutation = useMutation({
    mutationFn: () => acceptInvitation(token),
    onSuccess: () => navigate("/dashboard", { replace: true }),
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      setFormError(err.response?.data?.detail ?? "Could not accept the invitation."),
  })

  const validation = validationQuery.data
  const isAuthenticated = status === "authenticated"

  return (
    <div className="flex min-h-screen bg-white">
      <div className="flex w-full items-center justify-center px-6">
        <div className="w-full max-w-md">
          {validationQuery.isPending && <LoadingState label="Checking your invitation…" />}

          {validationQuery.isError && (
            <div className="text-center">
              <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-amber-100">
                <svg
                  className="size-6 text-amber-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.9 5h13.7a2 2 0 001.8-3l-6.85-12a2 2 0 00-3.5 0l-6.85 12a2 2 0 001.8 3z"
                  />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-slate-900">This invitation is no longer valid</h2>
              <p className="mt-2 text-sm text-slate-500">
                The link may have expired or already been used. Ask an admin to resend it.
              </p>
            </div>
          )}

          {!validationQuery.isPending && !validationQuery.isError && validation && (
            <div>
              <div className="mb-6 flex items-center gap-3">
                <NexoraLogo className="size-11 text-brand-600 shrink-0" />
                <span className="text-2xl font-bold text-slate-900">Nexora</span>
              </div>

              <h1 className="text-lg font-semibold text-slate-900">
                You're invited to <span className="text-brand-600">{validation.company_name}</span>
              </h1>
              <p className="mt-1.5 mb-8 text-sm text-slate-500">
                The invitation was sent to{" "}
                <span className="font-medium text-slate-700">{validation.email}</span> as{" "}
                <span className="font-medium capitalize text-slate-700">
                  {validation.role.toLowerCase()}
                </span>
                .
              </p>

              {validation.user_exists ? (
                <div>
                  {!isAuthenticated ? (
                    <div className="text-sm text-slate-600">
                      <p>
                        An account already exists for this email. Sign in to accept the invitation.
                      </p>
                      <Button className="mt-4 w-full" onClick={() => navigate("/login")}>
                        Sign in to accept
                      </Button>
                    </div>
                  ) : (
                    <div>
                      {user?.email !== validation.email && (
                        <div
                          role="alert"
                          className="mb-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700"
                        >
                          You're signed in as <strong>{user?.email}</strong>, but this invitation is
                          for <strong>{validation.email}</strong>. Sign out and sign in with the
                          invited email.
                        </div>
                      )}
                      {formError && (
                        <p role="alert" className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                          {formError}
                        </p>
                      )}
                      {user?.email === validation.email && (
                        <Button
                          className="w-full"
                          isLoading={acceptMutation.isPending}
                          onClick={() => acceptMutation.mutate()}
                        >
                          Accept invitation
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault()
                      setFormErrors({})
                      setFormError(null)
                      if (!first_name.trim()) {
                        setFormErrors((f) => ({ ...f, first_name: "First name is required." }))
                        return
                      }
                      if (password.length < 8) {
                        setFormErrors((f) => ({
                          ...f,
                          password: "Password must be at least 8 characters.",
                        }))
                        return
                      }
                      if (password !== confirmPassword) {
                        setFormErrors((f) => ({ ...f, confirm_password: "Passwords do not match." }))
                        return
                      }
                      registerMutation.mutate()
                    }}
                    className="space-y-4"
                  >
                    <div className="grid gap-4 sm:grid-cols-2">
                      <Input
                        label="First name"
                        value={first_name}
                        onChange={(e) => setFirstName(e.target.value)}
                        error={formErrors.first_name}
                        autoComplete="given-name"
                      />
                      <Input
                        label="Last name"
                        value={last_name}
                        onChange={(e) => setLastName(e.target.value)}
                        error={formErrors.last_name}
                        autoComplete="family-name"
                      />
                    </div>
                    <Input
                      label="Create a password"
                      type="password"
                      autoComplete="new-password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      error={formErrors.password}
                    />
                    <Input
                      label="Confirm password"
                      type="password"
                      autoComplete="new-password"
                      placeholder="••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      error={formErrors.confirm_password}
                    />
                    {formError && (
                      <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                        {formError}
                      </p>
                    )}
                    <Button type="submit" className="w-full" isLoading={registerMutation.isPending}>
                      Create account & accept
                    </Button>
                  </form>
                </div>
              )}
            </div>
          )}

          {!validationQuery.isPending && !token && <Navigate to="/login" replace />}
        </div>
      </div>
    </div>
  )
}
