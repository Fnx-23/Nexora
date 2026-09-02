import { useCallback, useRef, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  FileIcon,
  UploadIcon,
  DownloadIcon,
  TrashIcon,
  SearchIcon,
} from "@/components/icons"
import { Button } from "@/components/ui/Button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { Modal } from "@/components/ui/Modal"
import { LoadingState } from "@/components/ui/LoadingState"
import { useAuth } from "@/hooks/useAuth"
import {
  fetchDocuments,
  uploadDocument,
  renameDocument,
  deleteDocument,
} from "@/features/documents/api"
import { queryKeys } from "@/utils/queryKeys"
import type { EntityKind, Document } from "@/types/document"

const ACCEPT = ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.png,.jpg,.jpeg,.gif,.zip,.rar"

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

function mimeToLabel(mime: string): string {
  if (mime.includes("pdf")) return "PDF"
  if (mime.includes("word") || mime.includes("document")) return "DOC"
  if (mime.includes("sheet") || mime.includes("excel")) return "XLS"
  if (mime.includes("presentation") || mime.includes("powerpoint")) return "PPT"
  if (mime.startsWith("image/")) return "IMG"
  if (mime.startsWith("text/")) return "TXT"
  if (mime.includes("zip") || mime.includes("rar")) return "ZIP"
  return mime.split("/").pop()?.toUpperCase().slice(0, 4) ?? "FILE"
}

function mimeColor(mime: string): string {
  if (mime.includes("pdf")) return "bg-red-50 text-red-700"
  if (mime.includes("word") || mime.includes("document")) return "bg-brand-50 text-brand-700"
  if (mime.includes("sheet") || mime.includes("excel")) return "bg-emerald-50 text-emerald-700"
  if (mime.includes("presentation") || mime.includes("powerpoint")) return "bg-amber-50 text-amber-700"
  if (mime.startsWith("image/")) return "bg-violet-50 text-violet-700"
  return "bg-surface-100 text-surface-600"
}

interface DocumentManagerProps {
  entityKind: EntityKind
  entityId: string
  canDelete?: boolean
}

export function DocumentManager({
  entityKind,
  entityId,
  canDelete = false,
}: DocumentManagerProps) {
  const { activeCompany } = useAuth()
  const companyId = activeCompany?.id ?? null
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [search, setSearch] = useState("")
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null)
  const [renameTarget, setRenameTarget] = useState<Document | null>(null)
  const [renameValue, setRenameValue] = useState("")

  const docsQuery = useQuery({
    queryKey: [...queryKeys.documents(companyId), entityKind, entityId],
    queryFn: () =>
      fetchDocuments({ entity_kind: entityKind, entity_id: entityId, page_size: 100 }),
    enabled: companyId !== null,
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(file, entityKind, entityId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...queryKeys.documents(companyId), entityKind, entityId],
      })
    },
  })

  const renameMutation = useMutation({
    mutationFn: ({ id, filename }: { id: string; filename: string }) =>
      renameDocument(id, filename),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...queryKeys.documents(companyId), entityKind, entityId],
      })
      setRenameTarget(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...queryKeys.documents(companyId), entityKind, entityId],
      })
      setDeleteTarget(null)
    },
  })

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) uploadMutation.mutate(file)
      e.target.value = ""
    },
    [uploadMutation],
  )

  const handleDownload = useCallback((doc: Document) => {
    if (doc.url) {
      window.open(doc.url, "_blank")
    }
  }, [])

  const openRename = useCallback((doc: Document) => {
    setRenameTarget(doc)
    setRenameValue(doc.original_filename)
  }, [])

  const filteredDocs = docsQuery.data?.results.filter((d) =>
    search ? d.original_filename.toLowerCase().includes(search.toLowerCase()) : true,
  )

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Documents</CardTitle>
          <div className="flex items-center gap-2">
            <div className="relative">
              <SearchIcon className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-surface-400" />
              <input
                type="text"
                placeholder="Search files…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="h-8 w-48 rounded-md border border-surface-200 bg-white pl-8 pr-3 text-sm placeholder:text-surface-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500/20"
              />
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              isLoading={uploadMutation.isPending}
            >
              <UploadIcon className="mr-1.5 size-4" />
              Upload
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPT}
              className="hidden"
              onChange={handleFileChange}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {uploadMutation.isError && (
          <div role="alert" className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {(uploadMutation.error as Error).message || "Upload failed. Check file type and size."}
          </div>
        )}

        {docsQuery.isPending && <LoadingState label="Loading documents…" />}

        {!docsQuery.isPending && filteredDocs?.length === 0 && (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <FileIcon className="mb-3 size-10 text-surface-300" />
            <p className="text-sm font-medium text-surface-500">
              {search ? "No files match your search" : "No documents yet"}
            </p>
            {!search && (
              <p className="mt-1 text-xs text-surface-400">
                Click Upload to add files to this {entityKind.toLowerCase()}.
              </p>
            )}
          </div>
        )}

        {filteredDocs && filteredDocs.length > 0 && (
          <div className="divide-y divide-surface-100">
            {filteredDocs.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-3 px-1 py-3 first:pt-0 last:pb-0"
              >
                <span
                  className={`flex size-9 shrink-0 items-center justify-center rounded-md text-[10px] font-bold ${mimeColor(doc.mime_type)}`}
                >
                  {mimeToLabel(doc.mime_type)}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-surface-900">
                    {doc.original_filename}
                  </p>
                  <p className="text-xs text-surface-400">
                    {formatBytes(doc.size)} · {doc.uploaded_by_name} ·{" "}
                    {new Date(doc.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex shrink-0 gap-1">
                  {doc.url && (
                    <button
                      type="button"
                      onClick={() => handleDownload(doc)}
                      title="Download"
                      className="rounded-md p-1.5 text-surface-400 transition-colors hover:bg-surface-100 hover:text-surface-700"
                    >
                      <DownloadIcon className="size-4" />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => openRename(doc)}
                    title="Rename"
                    className="rounded-md p-1.5 text-surface-400 transition-colors hover:bg-surface-100 hover:text-surface-700"
                  >
                    <span className="text-xs font-medium">Rename</span>
                  </button>
                  {canDelete && (
                    <button
                      type="button"
                      onClick={() => setDeleteTarget(doc)}
                      title="Delete"
                      className="rounded-md p-1.5 text-surface-400 transition-colors hover:bg-red-50 hover:text-red-600"
                    >
                      <TrashIcon className="size-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      <Modal
        open={renameTarget !== null}
        onClose={() => setRenameTarget(null)}
        title="Rename file"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setRenameTarget(null)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (renameTarget && renameValue.trim()) {
                  renameMutation.mutate({
                    id: renameTarget.id,
                    filename: renameValue.trim(),
                  })
                }
              }}
              isLoading={renameMutation.isPending}
            >
              Rename
            </Button>
          </>
        }
      >
        <input
          type="text"
          value={renameValue}
          onChange={(e) => setRenameValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && renameValue.trim()) {
              renameMutation.mutate({
                id: renameTarget!.id,
                filename: renameValue.trim(),
              })
            }
          }}
          className="block w-full rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm shadow-sm placeholder:text-surface-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-0"
          autoFocus
        />
      </Modal>

      <Modal
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Delete file"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              isLoading={deleteMutation.isPending}
              onClick={() => {
                if (deleteTarget) deleteMutation.mutate(deleteTarget.id)
              }}
            >
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-surface-600">
          Are you sure you want to permanently delete{" "}
          <span className="font-medium text-surface-900">{deleteTarget?.original_filename}</span>?
          This action cannot be undone.
        </p>
      </Modal>
    </Card>
  )
}
