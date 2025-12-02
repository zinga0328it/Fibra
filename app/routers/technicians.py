"""
Technicians API router for Gestionale Fibra.

Provides CRUD endpoints for managing field technicians.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.technician import Technician
from app.schemas.technician import (
    TechnicianCreate,
    TechnicianListResponse,
    TechnicianResponse,
    TechnicianUpdate,
)
from app.security import get_api_key_header

router = APIRouter(
    prefix="/api/technicians",
    tags=["technicians"],
    dependencies=[Depends(get_api_key_header)],
)


@router.get("", response_model=TechnicianListResponse)
async def list_technicians(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    db: AsyncSession = Depends(get_db),
) -> TechnicianListResponse:
    """
    List all technicians with pagination and filtering.
    
    Args:
        page: Page number (1-indexed)
        size: Number of items per page
        is_active: Optional filter by active status
        team_id: Optional filter by team ID
        db: Database session
        
    Returns:
        TechnicianListResponse: Paginated list of technicians
    """
    query = select(Technician)
    count_query = select(func.count(Technician.id))
    
    if is_active is not None:
        query = query.where(Technician.is_active == is_active)
        count_query = count_query.where(Technician.is_active == is_active)
    
    if team_id is not None:
        query = query.where(Technician.team_id == team_id)
        count_query = count_query.where(Technician.team_id == team_id)
    
    # Get total count
    total = (await db.execute(count_query)).scalar()
    
    # Get paginated results
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Technician.name)
    result = await db.execute(query)
    technicians = result.scalars().all()
    
    return TechnicianListResponse(
        items=[TechnicianResponse.model_validate(t) for t in technicians],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/{technician_id}", response_model=TechnicianResponse)
async def get_technician(
    technician_id: int,
    db: AsyncSession = Depends(get_db),
) -> TechnicianResponse:
    """
    Get a specific technician by ID.
    
    Args:
        technician_id: Technician ID
        db: Database session
        
    Returns:
        TechnicianResponse: Technician details
        
    Raises:
        HTTPException: If technician not found
    """
    result = await db.execute(
        select(Technician).where(Technician.id == technician_id)
    )
    technician = result.scalar_one_or_none()
    
    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found",
        )
    
    return TechnicianResponse.model_validate(technician)


@router.post("", response_model=TechnicianResponse, status_code=status.HTTP_201_CREATED)
async def create_technician(
    data: TechnicianCreate,
    db: AsyncSession = Depends(get_db),
) -> TechnicianResponse:
    """
    Create a new technician.
    
    Args:
        data: Technician creation data
        db: Database session
        
    Returns:
        TechnicianResponse: Created technician
    """
    technician = Technician(**data.model_dump())
    db.add(technician)
    await db.flush()
    await db.refresh(technician)
    
    return TechnicianResponse.model_validate(technician)


@router.put("/{technician_id}", response_model=TechnicianResponse)
async def update_technician(
    technician_id: int,
    data: TechnicianUpdate,
    db: AsyncSession = Depends(get_db),
) -> TechnicianResponse:
    """
    Update a technician.
    
    Args:
        technician_id: Technician ID
        data: Update data
        db: Database session
        
    Returns:
        TechnicianResponse: Updated technician
        
    Raises:
        HTTPException: If technician not found
    """
    result = await db.execute(
        select(Technician).where(Technician.id == technician_id)
    )
    technician = result.scalar_one_or_none()
    
    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found",
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(technician, field, value)
    
    await db.flush()
    await db.refresh(technician)
    
    return TechnicianResponse.model_validate(technician)


@router.delete("/{technician_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_technician(
    technician_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a technician.
    
    Args:
        technician_id: Technician ID
        db: Database session
        
    Raises:
        HTTPException: If technician not found
    """
    result = await db.execute(
        select(Technician).where(Technician.id == technician_id)
    )
    technician = result.scalar_one_or_none()
    
    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found",
        )
    
    await db.delete(technician)


@router.get("/by-telegram/{telegram_id}", response_model=TechnicianResponse)
async def get_technician_by_telegram(
    telegram_id: str,
    db: AsyncSession = Depends(get_db),
) -> TechnicianResponse:
    """
    Get a technician by Telegram ID.
    
    Args:
        telegram_id: Telegram user ID
        db: Database session
        
    Returns:
        TechnicianResponse: Technician details
        
    Raises:
        HTTPException: If technician not found
    """
    result = await db.execute(
        select(Technician).where(Technician.telegram_id == telegram_id)
    )
    technician = result.scalar_one_or_none()
    
    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found",
        )
    
    return TechnicianResponse.model_validate(technician)
