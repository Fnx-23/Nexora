import type { ReactNode } from "react"

import { Button } from "@/components/ui/Button"
import { EmptyState } from "@/components/ui/EmptyState"

interface PlaceholderModuleProps {
  icon: ReactNode
  title: string
  description: string
  capabilities: readonly string[]
}

/**
 * Shared scaffold for modules that ship next. Renders the planned scope so
 * stakeholders can review direction before implementation starts.
 */
export function PlaceholderModule({ icon, title, description, capabilities }: PlaceholderModuleProps) {
  return (
    <div>
      <EmptyState
        icon={icon}
        title={`${title} is on the roadmap`}
        description={description}
        action={
          <Button variant="secondary" size="sm" disabled title="Not implemented yet">
            Coming soon
          </Button>
        }
      />
      <ul className="mx-auto -mt-8 mb-8 grid max-w-md list-disc space-y-1 text-left text-sm text-surface-500">
        {capabilities.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  )
}
