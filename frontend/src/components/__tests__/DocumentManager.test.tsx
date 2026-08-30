import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, within, waitFor } from "@testing-library/react"
import { fireEvent } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { DocumentManager } from "@/components/DocumentManager"
import * as docsApi from "@/features/documents/api"
import { useAuth } from "@/hooks/useAuth"
import type { Document } from "@/types/document"

vi.mock("@/hooks/useAuth")
vi.mock("@/features/documents/api")

const mockUseAuth = vi.mocked(useAuth)

const mockDocs: Document[] = [
  {
    id: "doc-1",
    original_filename: "spec.pdf",
    mime_type: "application/pdf",
    size: 102400,
    entity_kind: "PROJECT",
    entity_id: "proj-1",
    uploaded_by: "u1",
    uploaded_by_name: "Alice",
    url: "https://example.com/doc-1",
    created_at: "2025-01-15T10:00:00Z",
    updated_at: "2025-01-15T10:00:00Z",
  },
  {
    id: "doc-2",
    original_filename: "design.png",
    mime_type: "image/png",
    size: 204800,
    entity_kind: "PROJECT",
    entity_id: "proj-1",
    uploaded_by: "u1",
    uploaded_by_name: "Bob",
    url: "https://example.com/doc-2",
    created_at: "2025-01-16T11:00:00Z",
    updated_at: "2025-01-16T11:00:00Z",
  },
]

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

function renderWithProviders(ui: React.ReactNode) {
  const qc = createQueryClient()
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

beforeEach(() => {
  vi.clearAllMocks()
  mockUseAuth.mockReturnValue({
    status: "authenticated",
    user: {
      id: "u1",
      email: "alice@test.com",
      first_name: "Alice",
      last_name: "Anderson",
      avatar: null,
      full_name: "Alice Anderson",
    },
    activeCompany: { id: "c1", name: "Acme", slug: "acme" },
    role: "ADMIN",
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
  })
})

describe("DocumentManager", () => {
  it("renders loading state", () => {
    vi.mocked(docsApi.fetchDocuments).mockReturnValue(
      new Promise(() => {}),
    )
    renderWithProviders(
      <DocumentManager entityKind="PROJECT" entityId="proj-1" />,
    )
    expect(screen.getByText(/Loading documents/)).toBeInTheDocument()
  })

  it("renders empty state", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })
    renderWithProviders(
      <DocumentManager entityKind="PROJECT" entityId="proj-1" />,
    )
    await waitFor(() => {
      expect(screen.getByText("No documents yet")).toBeInTheDocument()
    })
  })

  it("renders documents", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: mockDocs,
    })
    renderWithProviders(
      <DocumentManager entityKind="PROJECT" entityId="proj-1" />,
    )
    await waitFor(() => {
      expect(screen.getByText("spec.pdf")).toBeInTheDocument()
      expect(screen.getByText("design.png")).toBeInTheDocument()
    })
    expect(screen.getByText(/Alice/)).toBeInTheDocument()
    expect(screen.getByText(/Bob/)).toBeInTheDocument()
  })

  it("renders Upload button", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })
    renderWithProviders(
      <DocumentManager entityKind="PROJECT" entityId="proj-1" />,
    )
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Upload/ }),
      ).toBeInTheDocument()
    })
  })

  it("shows delete buttons when canDelete is true", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockDocs[0]],
    })
    renderWithProviders(
      <DocumentManager
        entityKind="PROJECT"
        entityId="proj-1"
        canDelete
      />,
    )
    await waitFor(() => {
      expect(screen.getByTitle("Delete")).toBeInTheDocument()
    })
  })

  it("hides delete buttons when canDelete is false", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockDocs[0]],
    })
    renderWithProviders(
      <DocumentManager
        entityKind="PROJECT"
        entityId="proj-1"
        canDelete={false}
      />,
    )
    await waitFor(() => {
      expect(screen.getByText("spec.pdf")).toBeInTheDocument()
    })
    expect(screen.queryByTitle("Delete")).not.toBeInTheDocument()
  })

  it("filters documents by search", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: mockDocs,
    })
    renderWithProviders(
      <DocumentManager entityKind="PROJECT" entityId="proj-1" />,
    )
    await waitFor(() => {
      expect(screen.getByText("spec.pdf")).toBeInTheDocument()
    })
    await userEvent.type(
      screen.getByPlaceholderText(/Search files/),
      "png",
    )
    await waitFor(() => {
      expect(
        screen.queryByText("spec.pdf"),
      ).not.toBeInTheDocument()
      expect(screen.getByText("design.png")).toBeInTheDocument()
    })
  })

  it("displays search results empty state", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockDocs[0]],
    })
    renderWithProviders(
      <DocumentManager entityKind="PROJECT" entityId="proj-1" />,
    )
    await waitFor(() => {
      expect(screen.getByText("spec.pdf")).toBeInTheDocument()
    })
    await userEvent.type(
      screen.getByPlaceholderText(/Search files/),
      "nonexistent",
    )
    await waitFor(() => {
      expect(
        screen.getByText("No files match your search"),
      ).toBeInTheDocument()
    })
  })

  it("renders PDF badge for pdf files", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockDocs[0]],
    })
    renderWithProviders(
      <DocumentManager entityKind="PROJECT" entityId="proj-1" />,
    )
    await waitFor(() => {
      expect(screen.getByText("PDF")).toBeInTheDocument()
    })
  })

  it("renders IMG badge for image files", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockDocs[1]],
    })
    renderWithProviders(
      <DocumentManager entityKind="PROJECT" entityId="proj-1" />,
    )
    await waitFor(() => {
      expect(screen.getByText("IMG")).toBeInTheDocument()
    })
  })

  it("displays file sizes", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockDocs[0]],
    })
    renderWithProviders(
      <DocumentManager entityKind="PROJECT" entityId="proj-1" />,
    )
    await waitFor(() => {
      expect(screen.getByText(/100 KB/)).toBeInTheDocument()
    })
  })

  it("opens delete confirmation modal", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockDocs[0]],
    })
    renderWithProviders(
      <DocumentManager
        entityKind="PROJECT"
        entityId="proj-1"
        canDelete
      />,
    )
    await waitFor(() => {
      expect(screen.getByTitle("Delete")).toBeInTheDocument()
    })
    await userEvent.click(screen.getByTitle("Delete"))
    await waitFor(() => {
      const dialog = screen.getByRole("dialog")
      expect(within(dialog).getByText("Delete file")).toBeInTheDocument()
      expect(within(dialog).getByText(/spec\.pdf/)).toBeInTheDocument()
    })
  })

  it("calls deleteDocument on confirm", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockDocs[0]],
    })
    vi.mocked(docsApi.deleteDocument).mockResolvedValue(undefined)
    renderWithProviders(
      <DocumentManager
        entityKind="PROJECT"
        entityId="proj-1"
        canDelete
      />,
    )
    await waitFor(() => {
      expect(screen.getByTitle("Delete")).toBeInTheDocument()
    })
    await userEvent.click(screen.getByTitle("Delete"))
    await waitFor(() => {
      expect(screen.getByText("Delete file")).toBeInTheDocument()
    })
    const dialog = screen.getByRole("dialog")
    const deleteBtn = within(dialog).getByRole("button", {
      name: /^Delete$/,
    })
    await userEvent.click(deleteBtn)
    await waitFor(() => {
      expect(docsApi.deleteDocument).toHaveBeenCalledTimes(1)
      expect(vi.mocked(docsApi.deleteDocument).mock.calls[0][0]).toBe("doc-1")
    })
  })

  it("opens rename modal on rename click", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockDocs[0]],
    })
    renderWithProviders(
      <DocumentManager entityKind="PROJECT" entityId="proj-1" />,
    )
    await waitFor(() => {
      expect(screen.getByText("Rename")).toBeInTheDocument()
    })
    await userEvent.click(screen.getByText("Rename"))
    await waitFor(() => {
      expect(screen.getByText("Rename file")).toBeInTheDocument()
      expect(
        screen.getByDisplayValue("spec.pdf"),
      ).toBeInTheDocument()
    })
  })

  it("calls renameDocument on save", async () => {
    vi.mocked(docsApi.fetchDocuments).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockDocs[0]],
    })
    vi.mocked(docsApi.renameDocument).mockResolvedValue({
      ...mockDocs[0],
      original_filename: "updated.pdf",
    })
    renderWithProviders(
      <DocumentManager entityKind="PROJECT" entityId="proj-1" />,
    )
    await waitFor(() => {
      expect(screen.getByText("Rename")).toBeInTheDocument()
    })
    await userEvent.click(screen.getByText("Rename"))
    await waitFor(() => {
      expect(
        screen.getByDisplayValue("spec.pdf"),
      ).toBeInTheDocument()
    })
    const input = screen.getByDisplayValue("spec.pdf")
    fireEvent.change(input, { target: { value: "updated.pdf" } })
    const dialog = screen.getByRole("dialog")
    const renameBtn = within(dialog).getByRole("button", {
      name: /^Rename$/,
    })
    await userEvent.click(renameBtn)
    await waitFor(() => {
      expect(docsApi.renameDocument).toHaveBeenCalledTimes(1)
      expect(vi.mocked(docsApi.renameDocument).mock.calls[0][0]).toBe("doc-1")
      expect(vi.mocked(docsApi.renameDocument).mock.calls[0][1]).toBe("updated.pdf")
    })
  })
})
