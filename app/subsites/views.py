from fastapi import Depends, APIRouter, Query, Response, Body, HTTPException
from sqlmodel import select
from app.db import get_session, AsyncSession
from app.subsites.models import (
    SubSite,
    SubSiteCreate,
    SubSiteRead,
    SubSiteUpdate,
)
from uuid import UUID
from sqlalchemy import func
import json

router = APIRouter()


@router.get("/{subsite_id}", response_model=SubSiteRead)
async def get_subsite(
    session: AsyncSession = Depends(get_session),
    *,
    subsite_id: UUID,
) -> SubSiteRead:
    """Get an subsite by id"""
    res = await session.execute(
        select(SubSite).where(SubSite.id == subsite_id)
    )
    subsite = res.scalars().one_or_none()

    return subsite


@router.get("", response_model=list[SubSiteRead])
async def get_subsites(
    response: Response,
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get all subsites"""

    sort = json.loads(sort) if sort else []
    range = json.loads(range) if range else []
    filter = json.loads(filter) if filter else {}

    # Do a query to satisfy total count for "Content-Range" header
    count_query = select(func.count(SubSite.iterator))
    if len(filter):  # Have to filter twice for some reason? SQLModel state?
        for field, value in filter.items():
            if isinstance(value, list):
                count_query = count_query.where(
                    getattr(SubSite, field).in_(value)
                )
            elif field == "id" or field == "site_id":
                count_query = count_query.where(
                    getattr(SubSite, field) == value
                )
            else:
                count_query = count_query.where(
                    getattr(SubSite, field).like(f"%{value}%")
                )

    # Execute total count query (including filter)
    total_count_query = await session.execute(count_query)
    total_count = total_count_query.scalar_one()

    query = select(SubSite)
    # Order by sort field params ie. ["name","ASC"]
    if len(sort) == 2:
        sort_field, sort_order = sort
        if sort_order == "ASC":
            query = query.order_by(getattr(SubSite, sort_field))
        else:
            query = query.order_by(getattr(SubSite, sort_field).desc())

    # Filter by filter field params ie. {"name":"bar"}
    if len(filter):
        for field, value in filter.items():
            if isinstance(value, list):
                query = query.where(getattr(SubSite, field).in_(value))
            elif field == "id" or field == "site_id":
                query = query.where(getattr(SubSite, field) == value)
            else:
                query = query.where(getattr(SubSite, field).like(f"%{value}%"))

    if len(range) == 2:
        start, end = range
        query = query.offset(start).limit(end - start + 1)
    else:
        start, end = [0, total_count]  # For content-range header
    # Execute query
    results = await session.execute(query)
    subsites = results.scalars().all()

    response.headers["Content-Range"] = f"subsites {start}-{end}/{total_count}"

    return subsites


@router.post("", response_model=SubSiteRead)
async def create_subsite(
    subsite: SubSiteCreate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> SubSiteRead:
    """Creates an subsite"""
    print(subsite)
    subsite = SubSite.from_orm(subsite)
    session.add(subsite)
    await session.commit()
    await session.refresh(subsite)

    return subsite


@router.put("/{subsite_id}")
async def update_subsite(
    subsite_id: UUID,
    subsite_update: SubSiteUpdate,
    session: AsyncSession = Depends(get_session),
) -> SubSiteRead:
    res = await session.execute(
        select(SubSite).where(SubSite.id == subsite_id)
    )
    subsite_db = res.scalars().one()
    subsite_data = subsite_update.dict(exclude_unset=True)
    print(subsite_data)

    if not subsite_db:
        raise HTTPException(status_code=404, detail="SubSite not found")

    # Update the fields from the request
    for field, value in subsite_data.items():
        print(f"Updating: {field}, {value}")
        setattr(subsite_db, field, value)

    session.add(subsite_db)

    await session.commit()
    await session.refresh(subsite_db)

    return subsite_db


@router.delete("/{subsite_id}")
async def delete_subsite(
    subsite_id: UUID,
    session: AsyncSession = Depends(get_session),
    filter: dict[str, str] | None = None,
) -> None:
    """Delete an subsite by id"""
    res = await session.execute(
        select(SubSite).where(SubSite.id == subsite_id)
    )
    subsite = res.scalars().one_or_none()

    if subsite:
        await session.delete(subsite)
        await session.commit()
