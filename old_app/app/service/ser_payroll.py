from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.models.m_payroll import PayrollEntry
from app.db.models.m_payroll import PayrollPeriod
from app.db.models.m_payroll import PayrollSchedule
from app.db.models.m_employee import Employee
from app.schemas.sch_payroll import PayrollEntryCreate, PayrollPeriodCreate, PayrollScheduleCreate


# ---- PAYROLL SCHEDULE OPERATIONS ----

async def create_schedule(data: PayrollScheduleCreate, db: AsyncSession):
    """Create a new payroll schedule."""
    
    # Validate frequency
    valid_frequencies = ["weekly", "biweekly", "monthly"]
    if data.frequency.lower() not in valid_frequencies:
        raise HTTPException(
            status_code=400,
            detail=f"Frequency must be one of: {', '.join(valid_frequencies)}"
        )
    
    # Validate effective dates
    if data.effective_to and data.effective_from >= data.effective_to:
        raise HTTPException(
            status_code=400,
            detail="Effective from date must be before effective to date"
        )
    
    schedule = PayrollSchedule(
        frequency=data.frequency.lower(),
        anchor_date=data.anchor_date,
        pay_date_offset_days=data.pay_date_offset_days,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
        status="active"
    )
    
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    
    return schedule


async def get_schedule(schedule_id: UUID, db: AsyncSession):
    """Get payroll schedule by ID."""
    schedule = await db.get(PayrollSchedule, schedule_id)
    
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"Payroll schedule with ID {schedule_id} not found"
        )
    
    return schedule


async def list_schedules(db: AsyncSession, skip: int = 0, limit: int = 100):
    """List all payroll schedules with pagination."""
    result = await db.execute(
        select(PayrollSchedule).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def update_schedule(schedule_id: UUID, data: PayrollScheduleCreate, db: AsyncSession):
    """Update a payroll schedule."""
    schedule = await db.get(PayrollSchedule, schedule_id)
    
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"Payroll schedule with ID {schedule_id} not found"
        )
    
    # Validate frequency
    valid_frequencies = ["weekly", "biweekly", "monthly"]
    if data.frequency.lower() not in valid_frequencies:
        raise HTTPException(
            status_code=400,
            detail=f"Frequency must be one of: {', '.join(valid_frequencies)}"
        )
    
    # Validate effective dates
    if data.effective_to and data.effective_from >= data.effective_to:
        raise HTTPException(
            status_code=400,
            detail="Effective from date must be before effective to date"
        )
    
    # Update fields
    schedule.frequency = data.frequency.lower()
    schedule.anchor_date = data.anchor_date
    schedule.pay_date_offset_days = data.pay_date_offset_days
    schedule.effective_from = data.effective_from
    schedule.effective_to = data.effective_to
    
    await db.commit()
    await db.refresh(schedule)
    
    return schedule


async def deactivate_schedule(schedule_id: UUID, db: AsyncSession):
    """Deactivate a payroll schedule."""
    schedule = await db.get(PayrollSchedule, schedule_id)
    
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"Payroll schedule with ID {schedule_id} not found"
        )
    
    if schedule.status == "inactive":
        return schedule
    
    schedule.status = "inactive"
    await db.commit()
    await db.refresh(schedule)
    
    return schedule


# ---- PAYROLL PERIOD OPERATIONS ----

async def create_period(data: PayrollPeriodCreate, db: AsyncSession):
    """Create a new payroll period."""
    
    # Validate dates
    if data.start_date >= data.end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be before end date"
        )
    
    # Validate pay_date is after end_date
    if data.pay_date < data.end_date:
        raise HTTPException(
            status_code=400,
            detail="Pay date must be on or after the end date"
        )
    
    # Validate payroll schedule exists
    schedule_result = await db.execute(
        select(PayrollSchedule).where(PayrollSchedule.id == data.payroll_schedule_id)
    )
    schedule = schedule_result.scalars().first()
    
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"Payroll schedule with ID {data.payroll_schedule_id} not found"
        )
    
    period = PayrollPeriod(
        payroll_schedule_id=data.payroll_schedule_id,
        start_date=data.start_date,
        end_date=data.end_date,
        pay_date=data.pay_date,
        status="in_progress"
    )
    
    db.add(period)
    await db.commit()
    await db.refresh(period)
    
    return period


async def get_period(period_id: UUID, db: AsyncSession):
    """Get payroll period by ID."""
    period = await db.get(PayrollPeriod, period_id)
    
    if not period:
        raise HTTPException(
            status_code=404,
            detail=f"Payroll period with ID {period_id} not found"
        )
    
    return period


async def list_periods(db: AsyncSession, skip: int = 0, limit: int = 100):
    """List all payroll periods with pagination."""
    result = await db.execute(
        select(PayrollPeriod).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def finalize_period(period_id: UUID, db: AsyncSession):
    """Finalize a payroll period."""
    period = await db.get(PayrollPeriod, period_id)
    
    if not period:
        raise HTTPException(
            status_code=404,
            detail=f"Payroll period with ID {period_id} not found"
        )
    
    if period.status == "finalized":
        return period
    
    period.status = "finalized"
    await db.commit()
    await db.refresh(period)
    
    return period


# ---- PAYROLL ENTRY OPERATIONS ----

async def create_entry(data: PayrollEntryCreate, db: AsyncSession):
    """Create a new payroll entry with validation."""
    
    # Validate employee exists
    employee_result = await db.execute(
        select(Employee).where(Employee.id == data.employee_id)
    )
    employee = employee_result.scalars().first()
    
    if not employee:
        raise HTTPException(
            status_code=404,
            detail=f"Employee with ID {data.employee_id} not found"
        )
    
    # Validate payroll period exists
    period_result = await db.execute(
        select(PayrollPeriod).where(PayrollPeriod.id == data.payroll_period_id)
    )
    period = period_result.scalars().first()
    
    if not period:
        raise HTTPException(
            status_code=404,
            detail=f"Payroll period with ID {data.payroll_period_id} not found"
        )
    
    # Validate no duplicate entry for this employee in this period
    existing_result = await db.execute(
        select(PayrollEntry).where(
            (PayrollEntry.employee_id == data.employee_id) &
            (PayrollEntry.payroll_period_id == data.payroll_period_id)
        )
    )
    existing = existing_result.scalars().first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Payroll entry already exists for employee {data.employee_id} in this period"
        )
    
    # Create entry
    entry = PayrollEntry(**data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return entry


async def list_entries_by_period(period_id: UUID, db: AsyncSession):
    result = await db.execute(
        select(PayrollEntry).where(
            PayrollEntry.payroll_period_id == period_id
        )
    )
    return result.scalars().all()


async def finalize_entry(entry_id: UUID, db: AsyncSession):
    entry = await db.get(PayrollEntry, entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Payroll entry not found")

    if entry.status == "completed":
        return entry

    entry.status = "completed"

    await db.commit()
    await db.refresh(entry)

    return entry