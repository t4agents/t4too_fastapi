from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.db.db_async import get_db
from app.schemas.sch_payroll import (
    PayrollEntryCreate,
    PayrollEntryResponse,
    PayrollPeriodCreate,
    PayrollPeriodResponse,
    PayrollScheduleCreate,
    PayrollScheduleResponse,
)
from app.service.ser_payroll import (
    create_entry,
    list_entries_by_period,
    finalize_entry,
    create_period,
    get_period,
    list_periods,
    finalize_period,
    create_schedule,
    get_schedule,
    list_schedules,
    update_schedule,
    deactivate_schedule,
)

payrollRou = APIRouter()


# ---- PAYROLL SCHEDULE ENDPOINTS ----

@payrollRou.post(
    "/schedule",
    response_model=PayrollScheduleResponse,
    summary="Create a new payroll schedule",
    responses={
        201: {"description": "Payroll schedule created successfully"},
        400: {"description": "Invalid input data"},
    }
)
async def create_payroll_schedule(
    data: PayrollScheduleCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new payroll schedule with frequency, anchor date, and effective dates.
    
    Supported frequencies: weekly, biweekly, monthly
    """
    return await create_schedule(data, db)


@payrollRou.get(
    "/schedule/{schedule_id}",
    response_model=PayrollScheduleResponse,
    summary="Get a payroll schedule",
)
async def get_payroll_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific payroll schedule by ID.
    """
    return await get_schedule(schedule_id, db)


@payrollRou.get(
    "/schedules",
    response_model=List[PayrollScheduleResponse],
    summary="List all payroll schedules",
)
async def list_payroll_schedules(
    skip: int = Query(0, ge=0, description="Number of schedules to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum schedules to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all payroll schedules with pagination.
    """
    return await list_schedules(db, skip=skip, limit=limit)


@payrollRou.put(
    "/schedule/{schedule_id}",
    response_model=PayrollScheduleResponse,
    summary="Update a payroll schedule",
    responses={
        200: {"description": "Schedule updated successfully"},
        404: {"description": "Payroll schedule not found"},
        400: {"description": "Invalid input data"},
    }
)
async def update_payroll_schedule(
    schedule_id: UUID,
    data: PayrollScheduleCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing payroll schedule.
    """
    return await update_schedule(schedule_id, data, db)


@payrollRou.patch(
    "/schedule/{schedule_id}/deactivate",
    response_model=PayrollScheduleResponse,
    summary="Deactivate a payroll schedule",
    responses={
        200: {"description": "Schedule deactivated successfully"},
        404: {"description": "Payroll schedule not found"},
    }
)
async def deactivate_payroll_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a payroll schedule as inactive. It will no longer be used for new periods.
    """
    return await deactivate_schedule(schedule_id, db)


# ---- PAYROLL PERIOD ENDPOINTS ----

@payrollRou.post(
    "/period",
    response_model=PayrollPeriodResponse,
    summary="Create a new payroll period",
    responses={
        201: {"description": "Payroll period created successfully"},
        400: {"description": "Invalid date range"},
    }
)
async def create_payroll_period(
    data: PayrollPeriodCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new payroll period with start and end dates.
    
    The start_date must be before the end_date.
    """
    return await create_period(data, db)


@payrollRou.get(
    "/period/{period_id}",
    response_model=PayrollPeriodResponse,
    summary="Get a payroll period",
)
async def get_payroll_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific payroll period by ID.
    """
    return await get_period(period_id, db)


@payrollRou.get(
    "/periods",
    response_model=List[PayrollPeriodResponse],
    summary="List all payroll periods",
)
async def list_payroll_periods(
    skip: int = Query(0, ge=0, description="Number of periods to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum periods to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all payroll periods with pagination.
    """
    return await list_periods(db, skip=skip, limit=limit)


@payrollRou.patch(
    "/period/{period_id}/finalize",
    response_model=PayrollPeriodResponse,
    summary="Finalize a payroll period",
    responses={
        200: {"description": "Period finalized successfully"},
        404: {"description": "Payroll period not found"},
    }
)
async def finalize_payroll_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a payroll period as finalized. Cannot be changed after finalization.
    """
    return await finalize_period(period_id, db)


# ---- PAYROLL ENTRY ENDPOINTS ----

@payrollRou.post(
    "/entry",
    response_model=PayrollEntryResponse,
    summary="Create a new payroll entry",
    responses={
        201: {"description": "Payroll entry created successfully"},
        400: {"description": "Invalid input or duplicate entry"},
        404: {"description": "Employee or payroll period not found"},
    }
)
async def create_payroll_entry(
    data: PayrollEntryCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new payroll entry for an employee in a specific payroll period.
    
    Includes hours worked, hourly rates, deductions (CPP, EI, tax), and calculated totals.
    """
    return await create_entry(data, db)


@payrollRou.get(
    "/period/{period_id}/entries",
    response_model=List[PayrollEntryResponse],
    summary="Get all entries for a payroll period",
)
async def get_entries(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all payroll entries for a specific payroll period.
    """
    return await list_entries_by_period(period_id, db)


@payrollRou.patch(
    "/entry/{entry_id}/finalize",
    response_model=PayrollEntryResponse,
    summary="Finalize a payroll entry",
    responses={
        200: {"description": "Entry finalized successfully"},
        404: {"description": "Payroll entry not found"},
    }
)
async def complete_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a payroll entry as completed/finalized.
    """
    return await finalize_entry(entry_id, db)