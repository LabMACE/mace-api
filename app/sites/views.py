from fastapi import Depends, APIRouter, Query, Response, Body, HTTPException
from sqlmodel import select
from app.db import get_session, AsyncSession
from app.sites.models import Site, SiteCreate, SiteRead, SiteUpdate
from uuid import UUID
from sqlalchemy import func
import json

router = APIRouter()


@router.get("/{site_id}", response_model=SiteRead)
async def get_site(
    session: AsyncSession = Depends(get_session),
    *,
    site_id: UUID,
) -> SiteRead:
    """Get an site by id"""
    res = await session.execute(select(Site).where(Site.id == site_id))
    site = res.scalars().one_or_none()

    return site


@router.get("", response_model=list[SiteRead])
async def get_sites(
    response: Response,
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get all sites"""

    sort = json.loads(sort) if sort else []
    range = json.loads(range) if range else []
    filter = json.loads(filter) if filter else {}

    # Do a query to satisfy total count for "Content-Range" header
    count_query = select(func.count(Site.iterator))
    if len(filter):  # Have to filter twice for some reason? SQLModel state?
        for field, value in filter.items():
            if isinstance(value, list):
                count_query = count_query.where(
                    getattr(Site, field).in_(value)
                )
            elif field == "id" or field == "field_campaign_id":
                count_query = count_query.where(getattr(Site, field) == value)
            else:
                count_query = count_query.where(
                    getattr(Site, field).like(f"%{value}%")
                )

    # Execute total count query (including filter)
    total_count_query = await session.execute(count_query)
    total_count = total_count_query.scalar_one()

    query = select(Site)
    # Order by sort field params ie. ["name","ASC"]
    if len(sort) == 2:
        sort_field, sort_order = sort
        if sort_order == "ASC":
            query = query.order_by(getattr(Site, sort_field))
        else:
            query = query.order_by(getattr(Site, sort_field).desc())

    # Filter by filter field params ie. {"name":"bar"}
    if len(filter):
        for field, value in filter.items():
            if isinstance(value, list):
                query = query.where(getattr(Site, field).in_(value))
            elif field == "id" or field == "field_campaign_id":
                query = query.where(getattr(Site, field) == value)
            else:
                query = query.where(getattr(Site, field).like(f"%{value}%"))

    if len(range) == 2:
        start, end = range
        query = query.offset(start).limit(end - start + 1)
    else:
        start, end = [0, total_count]  # For content-range header

    # Execute query
    results = await session.execute(query)
    sites = results.scalars().all()

    response.headers["Content-Range"] = f"sites {start}-{end}/{total_count}"

    return sites


@router.post("", response_model=SiteRead)
async def create_site(
    site: SiteCreate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> SiteRead:
    """Creates an site"""
    print(site)
    site = Site.from_orm(site)
    session.add(site)
    await session.commit()
    await session.refresh(site)

    return site


@router.put("/{site_id}", response_model=SiteRead)
async def update_site(
    site_id: UUID,
    site_update: SiteUpdate,
    session: AsyncSession = Depends(get_session),
) -> SiteRead:
    res = await session.execute(select(Site).where(Site.id == site_id))
    site_db = res.scalars().one()
    site_data = site_update.dict(exclude_unset=True)

    if not site_db:
        raise HTTPException(status_code=404, detail="Site not found")

    # Update the fields from the request
    for field, value in site_data.items():
        if field == "latitude" or field == "longitude" or field == "elevation":
            # These fields should already be converted to geom in the
            # model, so skip
            continue
        print(f"Updating: {field}, {value}")
        setattr(site_db, field, value)

    session.add(site_db)
    await session.commit()
    await session.refresh(site_db)

    return site_db


@router.delete("/{site_id}")
async def delete_site(
    site_id: UUID,
    session: AsyncSession = Depends(get_session),
    filter: dict[str, str] | None = None,
) -> None:
    """Delete an site by id"""
    res = await session.execute(select(Site).where(Site.id == site_id))
    site = res.scalars().one_or_none()

    if site:
        await session.delete(site)
        await session.commit()
