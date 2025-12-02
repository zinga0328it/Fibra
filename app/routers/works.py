"""
Works API router for Gestionale Fibra.

Provides CRUD endpoints for managing work orders (WR).
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.work import Work, WorkStatus
from app.schemas.work import (
    WorkCreate,
    WorkListResponse,
    WorkResponse,
    WorkUpdate,
)
from app.security import get_api_key_header
from app.services.pdf_ocr import pdf_ocr_service

router = APIRouter(
    prefix="/api/works",
    tags=["works"],
    dependencies=[Depends(get_api_key_header)],
)


@router.get("", response_model=WorkListResponse)
async def list_works(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    status_filter: Optional[WorkStatus] = Query(None, alias="status", description="Filter by status"),
    operator: Optional[str] = Query(None, description="Filter by operator"),
    technician_id: Optional[int] = Query(None, description="Filter by technician"),
    date_from: Optional[date] = Query(None, description="Filter by scheduled date (from)"),
    date_to: Optional[date] = Query(None, description="Filter by scheduled date (to)"),
    db: AsyncSession = Depends(get_db),
) -> WorkListResponse:
    """
    List all work orders with pagination and filtering.
    
    Args:
        page: Page number (1-indexed)
        size: Number of items per page
        status_filter: Optional filter by work status
        operator: Optional filter by telecom operator
        technician_id: Optional filter by assigned technician
        date_from: Optional filter by scheduled date (start)
        date_to: Optional filter by scheduled date (end)
        db: Database session
        
    Returns:
        WorkListResponse: Paginated list of work orders
    """
    query = select(Work)
    count_query = select(func.count(Work.id))
    
    # Apply filters
    if status_filter is not None:
        query = query.where(Work.status == status_filter)
        count_query = count_query.where(Work.status == status_filter)
    
    if operator:
        query = query.where(Work.operator.ilike(f"%{operator}%"))
        count_query = count_query.where(Work.operator.ilike(f"%{operator}%"))
    
    if technician_id is not None:
        query = query.where(Work.technician_id == technician_id)
        count_query = count_query.where(Work.technician_id == technician_id)
    
    if date_from:
        query = query.where(Work.scheduled_date >= date_from)
        count_query = count_query.where(Work.scheduled_date >= date_from)
    
    if date_to:
        query = query.where(Work.scheduled_date <= date_to)
        count_query = count_query.where(Work.scheduled_date <= date_to)
    
    # Get total count
    total = (await db.execute(count_query)).scalar()
    
    # Get paginated results
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Work.scheduled_date.desc())
    result = await db.execute(query)
    works = result.scalars().all()
    
    return WorkListResponse(
        items=[WorkResponse.model_validate(w) for w in works],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/{work_id}", response_model=WorkResponse)
async def get_work(
    work_id: int,
    db: AsyncSession = Depends(get_db),
) -> WorkResponse:
    """
    Get a specific work order by ID.
    
    Args:
        work_id: Work order ID
        db: Database session
        
    Returns:
        WorkResponse: Work order details
        
    Raises:
        HTTPException: If work order not found
    """
    result = await db.execute(
        select(Work).where(Work.id == work_id)
    )
    work = result.scalar_one_or_none()
    
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )
    
    return WorkResponse.model_validate(work)


@router.post("", response_model=WorkResponse, status_code=status.HTTP_201_CREATED)
async def create_work(
    data: WorkCreate,
    db: AsyncSession = Depends(get_db),
) -> WorkResponse:
    """
    Create a new work order.
    
    Args:
        data: Work order creation data
        db: Database session
        
    Returns:
        WorkResponse: Created work order
    """
    # Check for duplicate WR number
    existing = await db.execute(
        select(Work).where(Work.wr_number == data.wr_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Work order with WR number {data.wr_number} already exists",
        )
    
    work = Work(**data.model_dump())
    
    # Set status based on technician assignment
    if work.technician_id:
        work.status = WorkStatus.ASSIGNED
    
    db.add(work)
    await db.flush()
    await db.refresh(work)
    
    return WorkResponse.model_validate(work)


@router.put("/{work_id}", response_model=WorkResponse)
async def update_work(
    work_id: int,
    data: WorkUpdate,
    db: AsyncSession = Depends(get_db),
) -> WorkResponse:
    """
    Update a work order.
    
    Args:
        work_id: Work order ID
        data: Update data
        db: Database session
        
    Returns:
        WorkResponse: Updated work order
        
    Raises:
        HTTPException: If work order not found
    """
    result = await db.execute(
        select(Work).where(Work.id == work_id)
    )
    work = result.scalar_one_or_none()
    
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(work, field, value)
    
    await db.flush()
    await db.refresh(work)
    
    return WorkResponse.model_validate(work)


@router.delete("/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work(
    work_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a work order.
    
    Args:
        work_id: Work order ID
        db: Database session
        
    Raises:
        HTTPException: If work order not found
    """
    result = await db.execute(
        select(Work).where(Work.id == work_id)
    )
    work = result.scalar_one_or_none()
    
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )
    
    await db.delete(work)


@router.post("/{work_id}/assign/{technician_id}", response_model=WorkResponse)
async def assign_work(
    work_id: int,
    technician_id: int,
    db: AsyncSession = Depends(get_db),
) -> WorkResponse:
    """
    Assign a work order to a technician.
    
    Args:
        work_id: Work order ID
        technician_id: Technician ID to assign
        db: Database session
        
    Returns:
        WorkResponse: Updated work order
        
    Raises:
        HTTPException: If work order not found
    """
    result = await db.execute(
        select(Work).where(Work.id == work_id)
    )
    work = result.scalar_one_or_none()
    
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )
    
    work.technician_id = technician_id
    work.status = WorkStatus.ASSIGNED
    
    await db.flush()
    await db.refresh(work)
    
    return WorkResponse.model_validate(work)


@router.post("/parse-pdf", response_model=dict)
async def parse_work_order_pdf(
    file: UploadFile = File(..., description="PDF file to parse"),
) -> dict:
    """
    Parse a work order PDF and extract information.
    
    Args:
        file: Uploaded PDF file
        
    Returns:
        dict: Extracted work order data
    """
    import tempfile
    import os
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF",
        )
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        extracted = await pdf_ocr_service.parse_work_order_async(tmp_path)
        return {
            "wr_number": extracted.wr_number,
            "operator": extracted.operator,
            "customer_name": extracted.customer_name,
            "customer_address": extracted.customer_address,
            "customer_phone": extracted.customer_phone,
            "scheduled_date": extracted.scheduled_date,
            "extra_data": extracted.extra_data,
        }
    finally:
        os.unlink(tmp_path)
