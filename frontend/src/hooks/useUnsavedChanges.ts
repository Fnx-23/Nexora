import { useCallback, useEffect, useRef, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"

export function useUnsavedChanges(isDirty: boolean) {
  const navigate = useNavigate()
  const location = useLocation()
  const [showConfirm, setShowConfirm] = useState(false)
  const pendingUrlRef = useRef<string | null>(null)

  useEffect(() => {
    if (!isDirty) return
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault()
    }
    window.addEventListener("beforeunload", handler)
    return () => window.removeEventListener("beforeunload", handler)
  }, [isDirty])

  useEffect(() => {
    if (!isDirty) return

    function onClick(event: MouseEvent) {
      if (event.defaultPrevented) return
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return

      const anchor = (event.target as HTMLElement | null)?.closest<HTMLAnchorElement>("a[href]")
      if (!anchor) return
      if (anchor.target && anchor.target !== "_self") return
      if (anchor.hasAttribute("download")) return

      const url = new URL(anchor.href, window.location.origin)
      if (url.origin !== window.location.origin) return
      if (url.pathname === location.pathname) return

      event.preventDefault()
      pendingUrlRef.current = url.pathname + url.search + url.hash
      setShowConfirm(true)
    }

    document.addEventListener("click", onClick, true)
    return () => document.removeEventListener("click", onClick, true)
  }, [isDirty, location.pathname])

  const handleConfirm = useCallback(() => {
    const url = pendingUrlRef.current
    pendingUrlRef.current = null
    setShowConfirm(false)
    if (url) {
      navigate(url)
    }
  }, [navigate])

  const handleCancel = useCallback(() => {
    pendingUrlRef.current = null
    setShowConfirm(false)
  }, [])

  return {
    showConfirm,
    handleConfirm,
    handleCancel,
  }
}