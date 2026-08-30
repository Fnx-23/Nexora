import { api } from "@/services/api"
import type { Paginated } from "@/types/api"
import type { Customer } from "@/types/customer"

export interface CustomerListParams {
  page?: number
  page_size?: number
  search?: string
  status?: string
  is_active?: boolean
  ordering?: string
}

export async function fetchCustomers(
  params: CustomerListParams = {},
): Promise<Paginated<Customer>> {
  const { data } = await api.get<Paginated<Customer>>("/customers/", { params })
  return data
}

export async function fetchCustomer(id: string): Promise<Customer> {
  const { data } = await api.get<Customer>(`/customers/${id}/`)
  return data
}

export interface CreateCustomerPayload {
  name: string
  company_name?: string
  email?: string
  phone?: string
  address?: string
  notes?: string
  status?: string
}

export async function createCustomer(
  payload: CreateCustomerPayload,
): Promise<Customer> {
  const { data } = await api.post<Customer>("/customers/", payload)
  return data
}

export async function updateCustomer(
  id: string,
  payload: Partial<CreateCustomerPayload>,
): Promise<Customer> {
  const { data } = await api.patch<Customer>(`/customers/${id}/`, payload)
  return data
}

export async function archiveCustomer(id: string): Promise<Customer> {
  const { data } = await api.post<Customer>(`/customers/${id}/archive/`)
  return data
}

export async function deleteCustomer(id: string): Promise<void> {
  await api.delete(`/customers/${id}/`)
}
