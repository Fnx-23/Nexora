import type { HTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from "react"

import { cn } from "@/utils/cn"

export function TableContainer({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("w-full overflow-x-auto rounded-xl border border-slate-200", className)} {...props} />
  )
}

export function Table({ className, ...props }: HTMLAttributes<HTMLTableElement>) {
  return <table className={cn("w-full border-collapse text-sm", className)} {...props} />
}

export function THead({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className={cn("bg-slate-50 [&>tr>th]:border-b [&>tr>th]:border-slate-200", className)}
      {...props}
    />
  )
}

export function TBody({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className={cn("[&>tr:hover]:bg-slate-50/70", className)} {...props} />
}

export function TR({ className, ...props }: HTMLAttributes<HTMLTableRowElement>) {
  return <tr className={cn("transition-colors", className)} {...props} />
}

export function TH({ className, ...props }: ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={cn(
        "px-5 py-3.5 text-left text-xs font-semibold tracking-wide text-slate-600 uppercase",
        className,
      )}
      {...props}
    />
  )
}

export function TD({ className, ...props }: TdHTMLAttributes<HTMLTableCellElement>) {
  return <td className={cn("border-b border-slate-100 px-5 py-4 align-middle", className)} {...props} />
}
