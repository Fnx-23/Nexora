
export interface SearchProject {
  id: string
  name: string
  status: string
  manager_name: string | null
  link: string
}

export interface SearchTask {
  id: string
  title: string
  status: string
  project_name: string | null
  assignee_name: string | null
  link: string
}

export interface SearchCustomer {
  id: string
  name: string
  company_name: string
  link: string
}

export interface SearchMember {
  id: string
  name: string
  email: string
  role: string
  link: string
}

export interface SearchResponse {
  query: string
  projects: SearchProject[]
  customers: SearchCustomer[]
  tasks: SearchTask[]
  members: SearchMember[]
}