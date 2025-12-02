"""
Teams API router for Gestionale Fibra.

Provides CRUD endpoints for managing technician teams.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.team import Team
from app.models.technician import Technician
from app.schemas.team import (
    TeamCreate,
    TeamListResponse,
    TeamResponse,
    TeamUpdate,
)
from app.security import get_api_key_header

router = APIRouter(
    prefix="/api/teams",
    tags=["teams"],
    dependencies=[Depends(get_api_key_header)],
)


@router.get("", response_model=TeamListResponse)
async def list_teams(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> TeamListResponse:
    """
    List all teams with pagination and filtering.
    
    Args:
        page: Page number (1-indexed)
        size: Number of items per page
        is_active: Optional filter by active status
        db: Database session
        
    Returns:
        TeamListResponse: Paginated list of teams
    """
    # Query with technician count
    query = (
        select(
            Team,
            func.count(Technician.id).label("technician_count"),
        )
        .outerjoin(Technician, Technician.team_id == Team.id)
        .group_by(Team.id)
    )
    
    count_query = select(func.count(Team.id))
    
    if is_active is not None:
        query = query.where(Team.is_active == is_active)
        count_query = count_query.where(Team.is_active == is_active)
    
    # Get total count
    total = (await db.execute(count_query)).scalar()
    
    # Get paginated results
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Team.name)
    result = await db.execute(query)
    rows = result.all()
    
    items = []
    for row in rows:
        team = row[0]
        tech_count = row[1]
        response = TeamResponse.model_validate(team)
        response.technician_count = tech_count
        items.append(response)
    
    return TeamListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """
    Get a specific team by ID.
    
    Args:
        team_id: Team ID
        db: Database session
        
    Returns:
        TeamResponse: Team details
        
    Raises:
        HTTPException: If team not found
    """
    result = await db.execute(
        select(
            Team,
            func.count(Technician.id).label("technician_count"),
        )
        .outerjoin(Technician, Technician.team_id == Team.id)
        .where(Team.id == team_id)
        .group_by(Team.id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    
    team = row[0]
    tech_count = row[1]
    response = TeamResponse.model_validate(team)
    response.technician_count = tech_count
    
    return response


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """
    Create a new team.
    
    Args:
        data: Team creation data
        db: Database session
        
    Returns:
        TeamResponse: Created team
    """
    team = Team(**data.model_dump())
    db.add(team)
    await db.flush()
    await db.refresh(team)
    
    response = TeamResponse.model_validate(team)
    response.technician_count = 0
    
    return response


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """
    Update a team.
    
    Args:
        team_id: Team ID
        data: Update data
        db: Database session
        
    Returns:
        TeamResponse: Updated team
        
    Raises:
        HTTPException: If team not found
    """
    result = await db.execute(
        select(Team).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)
    
    await db.flush()
    await db.refresh(team)
    
    # Get technician count
    count_result = await db.execute(
        select(func.count(Technician.id)).where(Technician.team_id == team_id)
    )
    tech_count = count_result.scalar()
    
    response = TeamResponse.model_validate(team)
    response.technician_count = tech_count
    
    return response


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a team.
    
    Args:
        team_id: Team ID
        db: Database session
        
    Raises:
        HTTPException: If team not found
    """
    result = await db.execute(
        select(Team).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    
    await db.delete(team)
