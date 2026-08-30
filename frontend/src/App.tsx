import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import { AuthProvider } from "@/contexts/AuthContext"
import { AppLayout } from "@/layouts/AppLayout"
import { LoginPage } from "@/features/auth/LoginPage"
import { ActivityPage } from "@/pages/ActivityPage"
import { ProjectDetailsPage } from "@/pages/ProjectDetailsPage"
import { CustomersPage } from "@/pages/CustomersPage"
import { DashboardPage } from "@/pages/DashboardPage"
import { NotFoundPage } from "@/pages/NotFoundPage"
import { ProjectsPage } from "@/pages/ProjectsPage"
import { SettingsPage } from "@/pages/SettingsPage"
import { TasksPage } from "@/pages/TasksPage"
import { TeamPage } from "@/pages/TeamPage"
import { TimeTrackingPage } from "@/pages/TimeTrackingPage"
import { ProtectedRoute } from "@/routes/ProtectedRoute"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (failureCount, error) => {
        // Never retry client errors (4xx); retry transient failures twice.
        const status = (error as { response?: { status?: number } }).response?.status
        if (status && status >= 400 && status < 500) return false
        return failureCount < 2
      },
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/projects" element={<ProjectsPage />} />
                <Route path="/projects/:id" element={<ProjectDetailsPage />} />
                <Route path="/customers" element={<CustomersPage />} />
                <Route path="/tasks" element={<TasksPage />} />
                <Route path="/time-tracking" element={<TimeTrackingPage />} />
                <Route path="/team" element={<TeamPage />} />
                <Route path="/activity" element={<ActivityPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>

            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
