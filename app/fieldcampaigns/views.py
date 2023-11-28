from fastapi import Depends, APIRouter, Query, Response, Body, HTTPException
from sqlmodel import select
from app.db import get_session, AsyncSession
from app.fieldcampaigns.models import (
    FieldCampaign,
    FieldCampaignCreate,
    FieldCampaignRead,
    FieldCampaignUpdate,
)
from uuid import UUID
from sqlalchemy import func
import json

router = APIRouter()


@router.get("/{field_campaign_id}", response_model=FieldCampaignRead)
async def get_field_campaign(
    session: AsyncSession = Depends(get_session),
    *,
    field_campaign_id: UUID,
) -> FieldCampaignRead:
    """Get an field_campaign by id"""
    res = await session.execute(
        select(FieldCampaign).where(FieldCampaign.id == field_campaign_id)
    )
    field_campaign = res.scalars().one_or_none()

    return field_campaign


@router.get("", response_model=list[FieldCampaignRead])
async def get_field_campaigns(
    response: Response,
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get all field campaigns"""

    sort = json.loads(sort) if sort else []
    range = json.loads(range) if range else []
    filter = json.loads(filter) if filter else {}

    query = select(FieldCampaign)

    # Do a query to satisfy total count for "Content-Range" header
    count_query = select(func.count(FieldCampaign.iterator))
    if len(filter):  # Have to filter twice for some reason? SQLModel state?
        for field, value in filter.items():
            for qry in [query, count_query]:  # Apply filter to both queries
                if isinstance(value, list):
                    qry = qry.where(getattr(FieldCampaign, field).in_(value))
                elif field == "id" or field == "field_campaign_id":
                    qry = qry.where(getattr(FieldCampaign, field) == value)
                else:
                    qry = qry.where(
                        getattr(FieldCampaign, field).like(f"%{value}%")
                    )

    # Execute total count query (including filter)
    total_count_query = await session.execute(count_query)
    total_count = total_count_query.scalar_one()

    # Order by sort field params ie. ["name","ASC"]
    if len(sort) == 2:
        sort_field, sort_order = sort
        if sort_order == "ASC":
            query = query.order_by(getattr(FieldCampaign, sort_field))
        else:
            query = query.order_by(getattr(FieldCampaign, sort_field).desc())

    # Filter by filter field params ie. {"name":"bar"}
    if len(filter):
        for field, value in filter.items():
            if isinstance(value, list):
                query = query.where(getattr(FieldCampaign, field).in_(value))
            elif field == "id" or field == "field_campaign_id":
                query = query.where(getattr(FieldCampaign, field) == value)
            else:
                query = query.where(
                    getattr(FieldCampaign, field).like(f"%{value}%")
                )

    if len(range) == 2:
        start, end = range
        query = query.offset(start).limit(end - start + 1)
    else:
        start, end = [0, total_count]  # For content-range header

    # Execute query
    results = await session.execute(query)
    field_campaigns = results.scalars().all()

    response.headers[
        "Content-Range"
    ] = f"field_campaigns {start}-{end}/{total_count}"
    return field_campaigns


@router.post("", response_model=FieldCampaignRead)
async def create_field_campaign(
    field_campaign: FieldCampaignCreate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> FieldCampaignRead:
    """Creates an field_campaign"""
    print(field_campaign)
    field_campaign = FieldCampaign.from_orm(field_campaign)
    session.add(field_campaign)
    await session.commit()
    await session.refresh(field_campaign)

    return field_campaign


@router.put("/{field_campaign_id}", response_model=FieldCampaignRead)
async def update_field_campaign(
    field_campaign_id: UUID,
    field_campaign_update: FieldCampaignUpdate,
    session: AsyncSession = Depends(get_session),
) -> FieldCampaignRead:
    res = await session.execute(
        select(FieldCampaign).where(FieldCampaign.id == field_campaign_id)
    )
    field_campaign_db = res.scalars().one()
    field_campaign_data = field_campaign_update.dict(exclude_unset=True)

    if not field_campaign_db:
        raise HTTPException(status_code=404, detail="FieldCampaign not found")

    # Update the fields from the request
    for field, value in field_campaign_data.items():
        print(f"Updating: {field}, {value}")
        setattr(field_campaign_db, field, value)

    session.add(field_campaign_db)
    await session.commit()
    await session.refresh(field_campaign_db)

    return field_campaign_db


@router.delete("/{field_campaign_id}")
async def delete_field_campaign(
    field_campaign_id: UUID,
    session: AsyncSession = Depends(get_session),
    filter: dict[str, str] | None = None,
) -> None:
    """Delete an field_campaign by id"""
    res = await session.execute(
        select(FieldCampaign).where(FieldCampaign.id == field_campaign_id)
    )
    field_campaign = res.scalars().one_or_none()

    if field_campaign:
        await session.delete(field_campaign)
        await session.commit()
