import { useCallback, useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { Navigate, useNavigate, useSearchParams } from "react-router-dom"

import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { NexoraLogo } from "@/components/NexoraLogo"
import { resetPassword } from "@/features/auth/securityApi"

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token")
  const token_id = searchParams.get("token_id") ?? searchParams.get("id")

  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const pathParts = window.location.pathname.split("/")
  const pathTokenId = pathParts[pathParts.length - 1]
  const resolvedTokenId = (token_id ?? pathTokenId) as string | null

  const mutation = useMutation({
    mutationFn: (data: { token_id: string; token: string; new_password: string; confirm_password: string }) =>
      resetPassword(data),
    onSuccess: () => {
      setSuccess(true)
      setError(null)
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      setError(err?.response?.data?.detail ?? "Invalid or expired token. Please request a new one.")
    },
  })

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      setError(null)
      setSuccess(false)
      if (newPassword !== confirmPassword) {
        setError("Passwords do not match.")
        return
      }
      if (!resolvedTokenId || !token) {
        setError("Missing token. Please use the link from your email.")
        return
      }
      mutation.mutate({
        token_id: resolvedTokenId,
        token,
        new_password: newPassword,
        confirm_password: confirmPassword,
      })
    },
    [newPassword, confirmPassword, token, resolvedTokenId, mutation],
  )

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white px-6">
        <div className="w-full max-w-sm text-center">
          <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-emerald-100">
            <svg className="size-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-slate-900">Password reset successfully</h2>
          <p className="mt-2 text-sm text-slate-500">
            Your password has been updated. You can now sign in with your new password.
          </p>
          <Button className="mt-6 w-full" onClick={() => navigate("/login")}>
            Sign in
          </Button>
        </div>
      </div>
    )
  }

  if (!resolvedTokenId || !token) {
    return <Navigate to="/forgot-password" replace />
  }

  return (
    <div className="flex min-h-screen">
      <div className="hidden w-1/2 flex-col justify-between bg-slate-900 p-12 lg:flex">
        <div className="flex items-center gap-3">
          <NexoraLogo className="size-12 text-brand-500 shrink-0" />
          <span className="text-2xl font-bold tracking-tight text-white">Nexora</span>
        </div>
        <div>
          <h1 className="max-w-md text-3xl font-semibold leading-tight text-white">
            Create a new password.
          </h1>
          <p className="mt-4 max-w-md text-slate-400">
            Your new password must be different from previously used passwords.
          </p>
        </div>
        <p className="text-xs text-slate-600">© 2026 Nexora</p>
      </div>

      <div className="flex w-full items-center justify-center bg-white px-6 lg:w-1/2">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <NexoraLogo className="size-10 text-brand-600 shrink-0" />
            <span className="text-xl font-bold text-slate-900">Nexora</span>
          </div>

          <h2 className="text-lg font-semibold text-slate-900">Reset password</h2>
          <p className="mt-1.5 mb-7 text-sm text-slate-500">
            Enter your new password below.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="New password"
              type="password"
              name="new_password"
              autoComplete="new-password"
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
            <Input
              label="Confirm new password"
              type="password"
              name="confirm_password"
              autoComplete="new-password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />

            {error && (
              <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </p>
            )}

            <Button type="submit" className="w-full" isLoading={mutation.isPending}>
              Reset password
            </Button>
          </form>

          <p className="mt-7 text-center text-xs text-slate-400">
            <a href="/login" className="text-brand-600 hover:underline">
              Back to sign in
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
