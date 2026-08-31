import { Link } from "react-router-dom"

import { Button } from "@/components/ui/Button"

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-surface-50 px-6 text-center">
      <p className="text-sm font-semibold text-brand-600">404</p>
      <h1 className="text-2xl font-semibold text-surface-900">Page not found</h1>
      <p className="max-w-sm text-sm text-surface-500">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link to="/dashboard">
        <Button variant="secondary">Back to dashboard</Button>
      </Link>
    </div>
  )
}
