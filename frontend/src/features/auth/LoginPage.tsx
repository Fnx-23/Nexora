import { useState, type FormEvent } from "react"
import { Navigate } from "react-router-dom"

import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { NexoraLogo } from "@/components/NexoraLogo"
import { useAuth } from "@/hooks/useAuth"
import { isAxiosErrorWithDetail } from "@/features/auth/errors"
import type { ApiErrorDetail } from "@/types/api"

export function LoginPage() {
  const { status, login } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (status === "authenticated") {
    return <Navigate to="/dashboard" replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await login(email.trim(), password)
    } catch (err) {
      setError(
        isAxiosErrorWithDetail(err)
          ? humanizeError(err.response?.data as ApiErrorDetail | undefined)
          : "Unable to sign in right now. Please try again.",
      )
    } finally {
      setIsSubmitting(false)
    }
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
            Run your whole business from one place.
          </h1>
          <p className="mt-4 max-w-md text-slate-400">
            Customers, projects, tasks, teams and reporting — built for small and
            medium-sized companies.
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

          <h2 className="text-lg font-semibold text-slate-900">Sign in to your workspace</h2>
          <p className="mt-1.5 mb-7 text-sm text-slate-500">
            Enter your work email and password.
          </p>

          <form onSubmit={(event) => void handleSubmit(event)} className="space-y-4">
            <Input
              label="Email"
              type="email"
              name="email"
              autoComplete="email"
              placeholder="you@company.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
            <Input
              label="Password"
              type="password"
              name="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />

            {error && (
              <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </p>
            )}

            <Button type="submit" className="w-full" isLoading={isSubmitting}>
              Sign in
            </Button>
          </form>

          <p className="mt-7 text-center text-xs text-slate-400">
            Company accounts are provisioned during onboarding.
          </p>
        </div>
      </div>
    </div>
  )
}

function humanizeError(detail: ApiErrorDetail | undefined): string {
  if (!detail) return "Invalid email or password."
  return typeof detail.detail === "string" ? detail.detail : "Invalid email or password."
}
