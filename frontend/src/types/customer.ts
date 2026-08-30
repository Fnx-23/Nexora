export type CustomerStatus = "ACTIVE" | "INACTIVE" | "ARCHIVED"

export interface Customer {
  id: string
  name: string
  company_name: string
  email: string
  phone: string
  address: string
  notes: string
  status: CustomerStatus
  is_active: boolean
  created_at: string
  updated_at: string
}
