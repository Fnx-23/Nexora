import { useCallback, useState } from "react"
import { useMutation } from "@tanstack/react-query"

import { Button } from "@/components/ui/Button"
import { Card, CardContent } from "@/components/ui/Card"
import { Input } from "@/components/ui/Input"
import { NexoraLogo } from "@/components/NexoraLogo"
import { forgotPassword } from "@/features/auth/securityApi"

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: forgotPassword,
    onSuccess: () => {
      setSubmitted(true)
      setError(null)
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      setError(err?.response?.data?.detail ?? "Something went wrong. Please try again.")
    },
  })

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      setError(null)
      setSubmitted(false)
      mutation.mutate({ email })
    },
    [email, mutation],
  )

  return (
    <div className="flex min-h-screen">
      <div className="hidden w-1/2 flex-col justify-between bg-slate-900 p-12 lg:flex">
        <div className="flex items-center gap-3">
          <NexoraLogo className="size-12 text-brand-500 shrink-0" />
          <span className="text-2xl font-bold tracking-tight text-white">Nexora</span>
        </div>
        <div>
          <h1 className="max-w-md text-3xl font-semibold leading-tight text-white">
            Recover your account.
          </h1>
          <p className="mt-4 max-w-md text-slate-400">
            Enter your work email and we'll send you a secure link to reset your password.
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

          <h2 className="text-lg font-semibold text-slate-900">Forgot your password?</h2>
          <p className="mt-1.5 mb-7 text-sm text-slate-500">
            No worries — we'll send you reset instructions.
          </p>

          {submitted ? (
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-slate-700">
                  If an account exists with that email, you'll receive a reset link shortly.
                  Check your inbox and spam folder.
                </p>
                <p className="mt-4 text-xs text-slate-400">
                  Remember your password?{" "}
                  <a href="/login" className="text-brand-600 hover:underline">
                    Sign in
                  </a>
                </p>
              </CardContent>
            </Card>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Email"
                type="email"
                name="email"
                autoComplete="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              {error && (
                <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                  {error}
                </p>
              )}

              <Button type="submit" className="w-full" isLoading={mutation.isPending}>
                Send reset link
              </Button>
            </form>
          )}

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
