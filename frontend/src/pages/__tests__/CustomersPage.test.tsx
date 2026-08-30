import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { CustomersPage } from "../CustomersPage"
import * as authHook from "@/hooks/useAuth"
import * as customersApi from "@/features/customers/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/customers/api", () => ({
  fetchCustomers: vi.fn(),
  createCustomer: vi.fn(),
  updateCustomer: vi.fn(),
  archiveCustomer: vi.fn(),
  deleteCustomer: vi.fn(),
}))

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

const MOCK_CUSTOMERS = [
  {
    id: "c1",
    name: "Alice Smith",
    company_name: "Globex Corp",
    email: "alice@globex.com",
    phone: "+1-555-0001",
    address: "1 Main St",
    notes: "",
    status: "ACTIVE" as const,
    is_active: true,
    created_at: "2025-01-15T10:00:00Z",
    updated_at: "2025-01-15T10:00:00Z",
  },
  {
    id: "c2",
    name: "Bob Jones",
    company_name: "Initech",
    email: "bob@initech.com",
    phone: "+1-555-0002",
    address: "",
    notes: "Important client",
    status: "INACTIVE" as const,
    is_active: false,
    created_at: "2025-02-20T14:00:00Z",
    updated_at: "2025-02-20T14:00:00Z",
  },
]

function mockAuth(role: "ADMIN" | "MANAGER" | "EMPLOYEE" = "ADMIN") {
  vi.mocked(authHook.useAuth).mockReturnValue({
    status: "authenticated",
    user: {
      id: "u1",
      email: "admin@test.com",
      first_name: "Admin",
      last_name: "Test",
      avatar: null,
      full_name: "Admin Test",
    },
    activeCompany: { id: "c1", name: "TestCo", slug: "testco" },
    role,
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
  })
}

function renderPage(queryClient?: QueryClient) {
  const qc = queryClient ?? makeQueryClient()
  return {
    qc,
    ...render(
      <MemoryRouter>
        <QueryClientProvider client={qc}>
          <CustomersPage />
        </QueryClientProvider>
      </MemoryRouter>,
    ),
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  vi.mocked(customersApi.fetchCustomers).mockResolvedValue({
    count: MOCK_CUSTOMERS.length,
    next: null,
    previous: null,
    results: MOCK_CUSTOMERS,
  })
})

describe("CustomersPage", () => {
  it("shows loading state", () => {
    vi.mocked(customersApi.fetchCustomers).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByText(/Loading customers/i)).toBeInTheDocument()
  })

  it("renders customer table with data", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument()
    })
    expect(screen.getByText("Bob Jones")).toBeInTheDocument()
    expect(screen.getByText("ACTIVE")).toBeInTheDocument()
    expect(screen.getByText("INACTIVE")).toBeInTheDocument()
  })

  it("shows customer count", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("2 customers")).toBeInTheDocument()
    })
  })

  it("shows error state on fetch failure", async () => {
    vi.mocked(customersApi.fetchCustomers).mockRejectedValue(new Error("Network"))
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Could not load customers")).toBeInTheDocument()
    })
  })

  it("shows empty state when no customers", async () => {
    vi.mocked(customersApi.fetchCustomers).mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("No customers found")).toBeInTheDocument()
    })
  })

  it("shows search input and status filter", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Search by name/i)).toBeInTheDocument()
    })
    expect(screen.getByDisplayValue("All statuses")).toBeInTheDocument()
  })

  it("Add customer button opens create modal", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Add customer")).toBeInTheDocument()
    })
    await user.click(screen.getByRole("button", { name: /add customer/i }))
    expect(screen.getByRole("dialog")).toBeInTheDocument()
    expect(screen.getByText("Add customer", { selector: "h2" })).toBeInTheDocument()
  })

  it("Edit button opens edit modal with customer data", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument()
    })

    const row = screen.getByText("Alice Smith").closest("tr")!
    const editBtn = within(row).getByRole("button", { name: "Edit" })
    await user.click(editBtn)

    expect(screen.getByRole("dialog")).toBeInTheDocument()
    expect(screen.getByText("Edit customer", { selector: "h2" })).toBeInTheDocument()
    expect(screen.getByDisplayValue("Alice Smith")).toBeInTheDocument()
    expect(screen.getByDisplayValue("Globex Corp")).toBeInTheDocument()
  })

  it("Archive button shows confirmation modal", async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument()
    })

    const row = screen.getByText("Alice Smith").closest("tr")!
    const archiveBtn = within(row).getByRole("button", { name: "Archive" })
    await user.click(archiveBtn)

    expect(screen.getByText("Archive customer", { selector: "h2" })).toBeInTheDocument()
    expect(screen.getByText(/Are you sure you want to archive/)).toBeInTheDocument()
  })

  it("EMPLOYEE role does not see archive button", async () => {
    mockAuth("EMPLOYEE")
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument()
    })

    const row = screen.getByText("Alice Smith").closest("tr")!
    expect(within(row).queryByRole("button", { name: "Archive" })).not.toBeInTheDocument()
  })

  it("ARCHIVED customers do not show archive button", async () => {
    vi.mocked(customersApi.fetchCustomers).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          ...MOCK_CUSTOMERS[0],
          status: "ARCHIVED",
          is_active: false,
        },
      ],
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument()
    })

    const row = screen.getByText("Alice Smith").closest("tr")!
    expect(within(row).queryByRole("button", { name: "Archive" })).not.toBeInTheDocument()
  })

  it("shows pagination when multiple pages", async () => {
    vi.mocked(customersApi.fetchCustomers).mockResolvedValue({
      count: 30,
      next: "http://test.com/api/v1/customers/?page=2",
      previous: null,
      results: MOCK_CUSTOMERS,
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Page 1 of 2")).toBeInTheDocument()
    })
    expect(screen.getByRole("button", { name: "Next" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Previous" })).toBeInTheDocument()
  })

  it("does not show pagination for single page", async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument()
    })
    expect(screen.queryByRole("button", { name: "Next" })).not.toBeInTheDocument()
  })
})
