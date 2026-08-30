"""Seed the database with realistic demo data for manual and e2e testing.

Usage::

    python manage.py seed_demo

The command is **idempotent** — running it multiple times will not create
duplicate records.  It uses deterministic lookups (company slug, user emails)
wrapped in ``get_or_create`` so subsequent runs are safe no-ops.

Demo data belongs exclusively to the *Nexora Demo* company.  Existing data
(including other companies, users, and all business records) is never modified
or deleted.
"""

from __future__ import annotations

from datetime import date, time, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.accounts.models import User
from apps.companies.models import Company, Membership, RoleChoices
from apps.customers.models import Customer
from apps.notifications.models import Notification
from apps.projects.models import Project, ProjectPriority, ProjectStatus
from apps.tasks.models import Task, TaskPriority, TaskStatus
from apps.time_tracking.models import TimeEntry

DEMO_COMPANY_NAME = "Nexora Demo"
DEMO_COMPANY_SLUG = slugify(DEMO_COMPANY_NAME)
DEMO_PASSWORD = "demo-2025!"  # documented; not a real secret

DEMO_USERS = [
    {
        "email": "admin@nexora.demo",
        "first_name": "Sara",
        "last_name": "Alami",
        "role": RoleChoices.ADMIN,
    },
    {
        "email": "manager@nexora.demo",
        "first_name": "Youssef",
        "last_name": "Benali",
        "role": RoleChoices.MANAGER,
    },
    {
        "email": "employee1@nexora.demo",
        "first_name": "Amina",
        "last_name": "Tazi",
        "role": RoleChoices.EMPLOYEE,
    },
    {
        "email": "employee2@nexora.demo",
        "first_name": "Omar",
        "last_name": "Fassi",
        "role": RoleChoices.EMPLOYEE,
    },
]

DEMO_CUSTOMERS = [
    {
        "name": "Karim Idrissi",
        "company_name": "Atlas Logistics",
        "email": "contact@atlaslogistics.demo",
        "phone": "+212-5-22-000-001",
        "address": "12 Rue des Fleurs, Casablanca, Morocco",
        "notes": "Key account — quarterly review scheduled.",
        "status": "ACTIVE",
    },
    {
        "name": "Leila Moussaoui",
        "company_name": "Nova Retail",
        "email": "info@novaretail.demo",
        "phone": "+212-5-22-000-002",
        "address": "45 Avenue Hassan II, Rabat, Morocco",
        "notes": "Expanding into e-commerce; high growth potential.",
        "status": "ACTIVE",
    },
    {
        "name": "Driss Chaoui",
        "company_name": "Horizon Labs",
        "email": "hello@horizonlabs.demo",
        "phone": "+212-5-22-000-003",
        "address": "8 Bd Mohammed V, Fes, Morocco",
        "notes": "R&D partnership; NDA in place.",
        "status": "ACTIVE",
    },
    {
        "name": "Fatima Zahra Berrada",
        "company_name": "Maghreb Digital",
        "email": "contact@maghrebdigital.demo",
        "phone": "+212-5-22-000-004",
        "address": "23 Rue Ouarzazate, Marrakech, Morocco",
        "notes": "Pending contract renewal.",
        "status": "INACTIVE",
    },
]


class Command(BaseCommand):
    help = "Seed realistic demo data for the Nexora Demo company."

    def handle(self, *args, **options):
        prev_eager = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)
        prev_backend = getattr(settings, "CELERY_RESULT_BACKEND", None)
        settings.CELERY_TASK_ALWAYS_EAGER = True
        settings.CELERY_RESULT_BACKEND = None
        try:
            with transaction.atomic():
                self._seed()
        finally:
            settings.CELERY_TASK_ALWAYS_EAGER = prev_eager
            settings.CELERY_RESULT_BACKEND = prev_backend

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _seed(self) -> None:
        company = self._get_or_create_company()
        users = self._get_or_create_users(company)
        admin = users["admin@nexora.demo"]
        manager = users["manager@nexora.demo"]
        employee1 = users["employee1@nexora.demo"]
        employee2 = users["employee2@nexora.demo"]

        customers = self._get_or_create_customers(company)
        projects = self._get_or_create_projects(company, customers, admin, manager, employee1)
        self._get_or_create_tasks(company, projects, admin, manager, employee1, employee2)
        self._get_or_create_time_entries(company, projects, employee1, employee2)
        self._get_or_create_notifications(company, admin, manager, employee1)

        self._print_summary()

    # ---- Company ----

    def _get_or_create_company(self) -> Company:
        company, created = Company.objects.get_or_create(
            slug=DEMO_COMPANY_SLUG,
            defaults={
                "name": DEMO_COMPANY_NAME,
                "description": "Demo workspace for testing and evaluation.",
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created company: {company.name}"))
        return company

    # ---- Users & Memberships ----

    def _get_or_create_users(self, company: Company) -> dict[str, User]:
        users: dict[str, User] = {}
        for spec in DEMO_USERS:
            user, created = User.objects.get_or_create(
                email=spec["email"],
                defaults={
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {user.email}"))

            membership, mem_created = Membership.objects.get_or_create(
                company=company,
                user=user,
                defaults={"role": spec["role"]},
            )
            if mem_created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created membership: {user.email} -> {company.name} ({spec['role']})"
                    )
                )

            users[spec["email"]] = user
        return users

    # ---- Customers ----

    def _get_or_create_customers(self, company: Company) -> list[Customer]:
        customers: list[Customer] = []
        for spec in DEMO_CUSTOMERS:
            customer, created = Customer.objects.get_or_create(
                company=company,
                company_name=spec["company_name"],
                defaults=spec,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created customer: {customer.company_name}"))
            customers.append(customer)
        return customers

    # ---- Projects ----

    def _get_or_create_projects(
        self,
        company: Company,
        customers: list[Customer],
        admin: User,
        manager: User,
        employee1: User,
    ) -> list[Project]:
        atlas = next(c for c in customers if c.company_name == "Atlas Logistics")
        nova = next(c for c in customers if c.company_name == "Nova Retail")
        horizon = next(c for c in customers if c.company_name == "Horizon Labs")

        today = date.today()

        project_specs = [
            {
                "name": "Cloud Infrastructure Migration",
                "description": "Migrate on-premise servers to AWS. Includes VPC setup, "
                "RDS migration, and CloudFront CDN configuration.",
                "customer": atlas,
                "manager": manager,
                "status": ProjectStatus.IN_PROGRESS,
                "priority": ProjectPriority.HIGH,
                "start_date": today - timedelta(days=30),
                "deadline": today + timedelta(days=60),
            },
            {
                "name": "E-commerce Platform",
                "description": "Build a modern e-commerce platform with product catalogue, "
                "cart, checkout, and payment integration.",
                "customer": nova,
                "manager": admin,
                "status": ProjectStatus.PLANNING,
                "priority": ProjectPriority.CRITICAL,
                "start_date": today + timedelta(days=14),
                "deadline": today + timedelta(days=120),
            },
            {
                "name": "Internal IT Portal",
                "description": "Self-service portal for internal IT requests: equipment, "
                "access provisioning, and incident tracking.",
                "customer": horizon,
                "manager": manager,
                "status": ProjectStatus.IN_PROGRESS,
                "priority": ProjectPriority.MEDIUM,
                "start_date": today - timedelta(days=15),
                "deadline": today + timedelta(days=45),
            },
        ]

        projects: list[Project] = []
        for spec in project_specs:
            project, created = Project.objects.get_or_create(
                company=company,
                name=spec["name"],
                defaults=spec,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created project: {project.name}"))
            projects.append(project)
        return projects

    # ---- Tasks ----

    def _get_or_create_tasks(
        self,
        company: Company,
        projects: list[Project],
        admin: User,
        manager: User,
        employee1: User,
        employee2: User,
    ) -> None:
        cloud, ecommerce, portal = projects

        today = date.today()

        task_specs = [
            # --- Cloud Infrastructure Migration ---
            {
                "title": "Set up AWS VPC and subnets",
                "description": "Configure VPC with public/private subnets across 2 AZs.",
                "project": cloud,
                "status": TaskStatus.DONE,
                "priority": TaskPriority.HIGH,
                "assignee": employee1,
                "created_by": manager,
                "due_date": today - timedelta(days=5),
            },
            {
                "title": "Migrate PostgreSQL to RDS",
                "description": "Schema migration, data transfer, and validation.",
                "project": cloud,
                "status": TaskStatus.IN_PROGRESS,
                "priority": TaskPriority.URGENT,
                "assignee": employee1,
                "created_by": manager,
                "due_date": today + timedelta(days=10),
            },
            {
                "title": "Configure CloudFront CDN",
                "description": "Set up distribution with custom domain and SSL.",
                "project": cloud,
                "status": TaskStatus.IN_REVIEW,
                "priority": TaskPriority.MEDIUM,
                "assignee": employee2,
                "created_by": manager,
                "due_date": today + timedelta(days=7),
            },
            {
                "title": "Write deployment runbook",
                "description": "Step-by-step guide for production cutover.",
                "project": cloud,
                "status": TaskStatus.TODO,
                "priority": TaskPriority.LOW,
                "assignee": employee2,
                "created_by": admin,
                "due_date": today + timedelta(days=20),
            },
            {
                "title": "Load testing with k6",
                "description": "Validate RDS performance under expected peak load.",
                "project": cloud,
                "status": TaskStatus.TODO,
                "priority": TaskPriority.MEDIUM,
                "assignee": None,
                "created_by": manager,
                "due_date": today + timedelta(days=15),
            },
            # --- E-commerce Platform ---
            {
                "title": "Design product catalogue schema",
                "description": "ERD for products, variants, categories, and pricing.",
                "project": ecommerce,
                "status": TaskStatus.IN_PROGRESS,
                "priority": TaskPriority.HIGH,
                "assignee": employee1,
                "created_by": admin,
                "due_date": today + timedelta(days=5),
            },
            {
                "title": "Implement shopping cart API",
                "description": "REST endpoints for add/remove/update cart items.",
                "project": ecommerce,
                "status": TaskStatus.TODO,
                "priority": TaskPriority.HIGH,
                "assignee": employee2,
                "created_by": admin,
                "due_date": today + timedelta(days=20),
            },
            {
                "title": "Integrate Stripe payments",
                "description": "Checkout session, webhook handling, refund flow.",
                "project": ecommerce,
                "status": TaskStatus.TODO,
                "priority": TaskPriority.URGENT,
                "assignee": None,
                "created_by": admin,
                "due_date": today + timedelta(days=40),
            },
            {
                "title": "Build admin dashboard UI",
                "description": "Product management, order overview, and analytics.",
                "project": ecommerce,
                "status": TaskStatus.TODO,
                "priority": TaskPriority.MEDIUM,
                "assignee": employee1,
                "created_by": admin,
                "due_date": today + timedelta(days=50),
            },
            # --- Internal IT Portal ---
            {
                "title": "User authentication module",
                "description": "SSO integration with company LDAP directory.",
                "project": portal,
                "status": TaskStatus.DONE,
                "priority": TaskPriority.HIGH,
                "assignee": employee2,
                "created_by": manager,
                "due_date": today - timedelta(days=10),
            },
            {
                "title": "Equipment request form",
                "description": "Dynamic form with approval workflow for hardware requests.",
                "project": portal,
                "status": TaskStatus.DONE,
                "priority": TaskPriority.MEDIUM,
                "assignee": employee1,
                "created_by": manager,
                "due_date": today - timedelta(days=3),
            },
            {
                "title": "Incident tracking board",
                "description": "Kanban-style board for IT incident management.",
                "project": portal,
                "status": TaskStatus.IN_REVIEW,
                "priority": TaskPriority.HIGH,
                "assignee": employee2,
                "created_by": manager,
                "due_date": today + timedelta(days=3),
            },
            {
                "title": "Access provisioning automation",
                "description": "Automated AD group membership based on role assignments.",
                "project": portal,
                "status": TaskStatus.IN_PROGRESS,
                "priority": TaskPriority.URGENT,
                "assignee": employee1,
                "created_by": manager,
                "due_date": today + timedelta(days=8),
            },
            {
                "title": "Knowledge base wiki",
                "description": "Internal docs for common IT procedures and FAQs.",
                "project": portal,
                "status": TaskStatus.TODO,
                "priority": TaskPriority.LOW,
                "assignee": employee2,
                "created_by": manager,
                "due_date": today + timedelta(days=25),
            },
            {
                "title": "SLA monitoring dashboard",
                "description": "Real-time SLA compliance tracking with alerting.",
                "project": portal,
                "status": TaskStatus.TODO,
                "priority": TaskPriority.MEDIUM,
                "assignee": None,
                "created_by": admin,
                "due_date": today + timedelta(days=30),
            },
        ]

        for spec in task_specs:
            task, created = Task.objects.get_or_create(
                company=company,
                title=spec["title"],
                defaults=spec,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created task: {task.title}"))

    # ---- Time entries ----

    def _get_or_create_time_entries(
        self,
        company: Company,
        projects: list[Project],
        employee1: User,
        employee2: User,
    ) -> None:
        cloud, ecommerce, portal = projects
        today = date.today()

        entry_specs = [
            # Employee1 — cloud project, recent days
            {
                "user": employee1,
                "project": cloud,
                "date": today - timedelta(days=2),
                "start_time": time(9, 0),
                "end_time": time(12, 30),
                "description": "RDS instance provisioning and security group setup.",
            },
            {
                "user": employee1,
                "project": cloud,
                "date": today - timedelta(days=1),
                "start_time": time(13, 0),
                "end_time": time(17, 0),
                "description": "Schema migration scripts and data validation queries.",
            },
            {
                "user": employee1,
                "project": ecommerce,
                "date": today,
                "start_time": time(9, 0),
                "end_time": time(11, 0),
                "description": "Product catalogue ERD review and initial Django models.",
            },
            # Employee2 — cloud and portal
            {
                "user": employee2,
                "project": cloud,
                "date": today - timedelta(days=1),
                "start_time": time(10, 0),
                "end_time": time(13, 0),
                "description": "CloudFront distribution configuration and testing.",
            },
            {
                "user": employee2,
                "project": portal,
                "date": today,
                "start_time": time(14, 0),
                "end_time": time(17, 30),
                "description": "Incident tracking board UI implementation.",
            },
        ]

        for spec in entry_specs:
            entry, created = TimeEntry.objects.get_or_create(
                company=company,
                user=spec["user"],
                project=spec["project"],
                date=spec["date"],
                start_time=spec["start_time"],
                defaults={
                    "end_time": spec["end_time"],
                    "description": spec["description"],
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created time entry: {spec['user'].first_name} "
                        f"- {spec['project'].name} - {spec['date']}"
                    )
                )

    # ---- Notifications (supplemental, beyond signal-generated ones) ----

    def _get_or_create_notifications(
        self,
        company: Company,
        admin: User,
        manager: User,
        employee1: User,
    ) -> None:
        """Create a few supplemental notifications that wouldn't be auto-generated."""
        supplemental = [
            {
                "recipient": admin,
                "actor": manager,
                "verb": "Monthly team performance report is ready for review.",
                "entity_type": "project",
                "entity_name": "Cloud Infrastructure Migration",
                "link": "/projects",
            },
            {
                "recipient": employee1,
                "actor": admin,
                "verb": "Welcome to Nexora Demo! Check your assigned tasks.",
                "entity_type": "",
                "entity_name": "",
                "link": "/tasks",
            },
            {
                "recipient": manager,
                "actor": admin,
                "verb": "Q3 planning session scheduled for next Monday.",
                "entity_type": "",
                "entity_name": "",
                "link": "/activity",
            },
        ]

        for spec in supplemental:
            _, created = Notification.objects.get_or_create(
                company=company,
                recipient=spec["recipient"],
                verb=spec["verb"],
                defaults={
                    "actor": spec["actor"],
                    "entity_type": spec["entity_type"],
                    "entity_name": spec["entity_name"],
                    "link": spec["link"],
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created notification for: {spec['recipient'].email}")
                )

    # ---- Summary ----

    def _print_summary(self) -> None:
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("  Demo seed complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"  Companies:      {Company.objects.count()}")
        self.stdout.write(f"  Users:          {User.objects.count()}")
        self.stdout.write(f"  Memberships:    {Membership.objects.count()}")
        self.stdout.write(f"  Customers:      {Customer.objects.count()}")
        self.stdout.write(f"  Projects:       {Project.objects.count()}")
        self.stdout.write(f"  Tasks:          {Task.objects.count()}")
        self.stdout.write(f"  Time entries:   {TimeEntry.objects.count()}")
        self.stdout.write(f"  Notifications:  {Notification.objects.count()}")
        self.stdout.write("")
        self.stdout.write(f"  Demo password:  {DEMO_PASSWORD}")
        self.stdout.write(self.style.SUCCESS("=" * 50))
