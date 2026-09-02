import { useEffect } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import { AuthProvider } from "@/contexts/AuthContext"
import { useAuth } from "@/hooks/useAuth"
import { AppLayout } from "@/layouts/AppLayout"
import { LoginPage } from "@/features/auth/LoginPage"
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage"
import { ResetPasswordPage } from "@/pages/ResetPasswordPage"
import { InvitePage } from "@/pages/InvitePage"
import { SettingsLayout } from "@/pages/SettingsLayout"
import { ActivityPage } from "@/pages/ActivityPage"
import { ProjectDetailsPage } from "@/pages/ProjectDetailsPage"
import { TaskDetailsPage } from "@/pages/TaskDetailsPage"
import { CustomersPage } from "@/pages/CustomersPage"
import { DashboardPage } from "@/pages/DashboardPage"
import { NotFoundPage } from "@/pages/NotFoundPage"
import { ProjectsPage } from "@/pages/ProjectsPage"
import { TasksPage } from "@/pages/TasksPage"
import { TeamPage } from "@/pages/TeamPage"
import { TimeTrackingPage } from "@/pages/TimeTrackingPage"
import { ReportsPage } from "@/pages/ReportsPage"
import { ProtectedRoute } from "@/routes/ProtectedRoute"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (failureCount, error) => {
        const status = (error as { response?: { status?: number } }).response?.status
        if (status && status >= 400 && status < 500) return false
        return failureCount < 2
      },
    },
  },
})

function LogoutRoute() {
  const { logout } = useAuth()
  useEffect(() => {
    logout()
  }, [logout])
  return null
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/logout" element={<LogoutRoute />} />
            <Route path="/register" element={<Navigate to="/login" replace />} />
            <Route path="/signup" element={<Navigate to="/login" replace />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password/:token_id" element={<ResetPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/invite/:token" element={<InvitePage />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/projects" element={<ProjectsPage />} />
                <Route path="/projects/:id" element={<ProjectDetailsPage />} />
                <Route path="/customers" element={<CustomersPage />} />
                <Route path="/tasks" element={<TasksPage />} />
                <Route path="/tasks/:id" element={<TaskDetailsPage />} />
                <Route path="/time-tracking" element={<TimeTrackingPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/team" element={<TeamPage />} />
                <Route path="/activity" element={<ActivityPage />} />
                <Route path="/settings" element={<SettingsLayout />} />
                <Route path="/settings/:tab" element={<SettingsLayout />} />
              </Route>
            </Route>

            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
