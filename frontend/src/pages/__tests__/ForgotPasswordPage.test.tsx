import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { ForgotPasswordPage } from "../ForgotPasswordPage"

vi.mock("@/features/auth/securityApi", () => ({
  forgotPassword: vi.fn().mockResolvedValue({ detail: "Sent" }),
}))

describe("ForgotPasswordPage", () => {
  function makeQueryClient() {
    return new QueryClient({ defaultOptions: { queries: { retry: false } } })
  }

  function renderPage() {
    return render(
      <QueryClientProvider client={makeQueryClient()}>
        <ForgotPasswordPage />
      </QueryClientProvider>,
    )
  }

  it("renders the email input", () => {
    renderPage()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
  })

  it("renders the submit button", () => {
    renderPage()
    expect(screen.getByRole("button", { name: /send reset link/i })).toBeInTheDocument()
  })

  it("shows success message after submit", async () => {
    const user = userEvent.setup()
    renderPage()
    const input = screen.getByLabelText(/email/i)
    await user.type(input, "test@example.com")
    await user.click(screen.getByRole("button", { name: /send reset link/i }))
    await screen.findByText(/if an account exists/i)
  })
})
