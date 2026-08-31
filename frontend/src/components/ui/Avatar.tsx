import { cn } from "@/utils/cn"

type AvatarSize = "xs" | "sm" | "md" | "lg"

const sizeClasses: Record<AvatarSize, string> = {
  xs: "size-7 text-[11px]",
  sm: "size-9 text-xs",
  md: "size-10 text-sm",
  lg: "size-12 text-base",
}

const palette = [
  "bg-brand-600",
  "bg-emerald-600",
  "bg-sky-600",
  "bg-violet-600",
  "bg-rose-600",
  "bg-amber-600",
]

function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return "?"
  const first = parts[0][0] ?? ""
  const second = parts.length > 1 ? (parts[1][0] ?? "") : ""
  return (first + second).toUpperCase()
}

function colorFor(name: string): string {
  let hash = 0
  for (const char of name) {
    hash = (hash * 31 + char.charCodeAt(0)) | 0
  }
  return palette[Math.abs(hash) % palette.length]
}

export interface AvatarProps {
  name: string
  src?: string | null
  size?: AvatarSize
  className?: string
}

export function Avatar({ name, src, size = "md", className }: AvatarProps) {
  return (
    <span
      title={name}
      className={cn(
        "inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full font-medium text-white select-none",
        sizeClasses[size],
        !src && colorFor(name),
        className,
      )}
    >
      {src ? (
        <img src={src} alt={name} className="size-full object-cover" />
      ) : (
        initialsOf(name)
      )}
    </span>
  )
}
