from typing import List, Optional, Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.models.m_employee import Employee


class EmployeeRepository:
    def __init__(self, db: AsyncSession, tenant_id: UUID, client_ids: Sequence[UUID]):
        self.db = db
        self.tenant_id = tenant_id
        self.client_ids = client_ids

    # ---- CREATE ----
    async def create(self, employee: Employee) -> Employee:
        """Create a new employee."""
        self.db.add(employee)
        # Transaction is managed by request-scoped dependency (get_db_w_session).
        # Flush to push SQL and populate PK without closing the outer transaction.
        await self.db.flush()
        await self.db.refresh(employee)
        return employee

    def _scoped_query(self):
        if not self.client_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No client access configured for current user",
            )
        return select(Employee).where(
            Employee.id == self.tenant_id,
            Employee.biz_id.in_(self.client_ids),
        )

    # ---- READ ----
    async def get_by_id(self, employee_id: UUID) -> Optional[Employee]:
        """Get employee by ID."""
        query = self._scoped_query()
        result = await self.db.execute(
            query.where((Employee.id == employee_id) & (Employee.is_deleted != True))
        )
        return result.scalars().first()

    async def get_by_sin(self, sin: str) -> Optional[Employee]:
        """Get employee by SIN (Social Insurance Number)."""
        query = self._scoped_query()
        result = await self.db.execute(
            query.where((Employee.sin == sin) & (Employee.is_deleted != True))
        )
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[Employee]:
        """Get employee by email."""
        query = self._scoped_query()
        result = await self.db.execute(
            query.where((Employee.email == email) & (Employee.is_deleted != True))
        )
        return result.scalars().first()


    async def get_by_name(self, first_name: str, last_name: str) -> List[Employee]:
        """Get employees by first and last name."""
        query = self._scoped_query()
        result = await self.db.execute(
            query.where(
                (Employee.first_name.ilike(f"%{first_name}%")) &
                (Employee.last_name.ilike(f"%{last_name}%")) &
                (Employee.is_deleted != True)
            )
        )
        return list(result.scalars().all())

    # ---- UPDATE ----
    async def update(self, employee_id: UUID, data: dict) -> Optional[Employee]:
        """Update employee by ID."""
        employee = await self.get_by_id(employee_id)
        if not employee:
            return None

        immutable_fields = {"biz_id", "ten_id", "owner_id"}
        for key, value in data.items():
            if key in immutable_fields:
                continue
            if value is not None:
                setattr(employee, key, value)

        await self.db.flush()
        await self.db.refresh(employee)
        return employee

    # ---- DELETE ----
    async def delete(self, employee_id: UUID) -> bool:
        """Soft delete employee by ID."""
        employee = await self.get_by_id(employee_id)
        if not employee:
            return False

        employee.is_deleted = True
        await self.db.flush()
        return True

    async def count(self) -> int:
        """Get total count of active employees."""
        query = self._scoped_query()
        result = await self.db.execute(
            query.where(Employee.is_deleted != True)
        )
        return len(result.scalars().all())
