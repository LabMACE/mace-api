from fastapi import Depends, APIRouter, Query, Response, Body, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from sqlmodel import select
from app.db import get_session, AsyncSession
from app.licor.models import (
    LICORData,
    LICORDataCreate,
    LICORDataRead,
    LICORDataUpdate,
    LICORDataset,
    LICORDataReadWithMeasurements,
)
from uuid import UUID
from sqlalchemy import func
from app.utils import decode_base64
import orjson
import datetime

router = APIRouter()


@router.get("/{licor_id}", response_model=LICORDataReadWithMeasurements)
async def get_licor(
    session: AsyncSession = Depends(get_session),
    *,
    licor_id: UUID,
) -> LICORDataReadWithMeasurements:
    """Get a licor record by id"""
    res = await session.execute(
        select(LICORData).where(LICORData.id == licor_id)
    )
    licor = res.scalars().one_or_none()
    datasets = []
    for dataset in licor.data["datasets"]:
        for key, measurements in dataset.items():
            datasets.append(
                {
                    "key": key,
                    "measurements": measurements,
                    "licor_id": licor_id,
                }
            )

    obj = LICORDataReadWithMeasurements(
        id=licor.id,
        name=licor.name,
        description=licor.description,
        created_at=licor.created_at,
        recorded_at=licor.recorded_at,
        measurements=datasets,
    )
    return obj


@router.get("/{licor_id}/data")
async def download_licor_data_as_file(
    session: AsyncSession = Depends(get_session),
    *,
    licor_id: UUID,
) -> StreamingResponse:
    """Get a licor record by id and return as the original .json file"""

    res = await session.execute(
        select(LICORData).where(LICORData.id == licor_id)
    )
    licor = res.scalars().one_or_none()

    return licor.data


@router.get("/{licor_id}/dataset/{dataset_id}", response_model=LICORDataset)
async def get_licor_Dataset(
    session: AsyncSession = Depends(get_session),
    *,
    licor_id: UUID,
    dataset_id: str,
) -> LICORDataset:
    """Get a dataset of a licor record"""

    res = await session.execute(
        select(LICORData).where(LICORData.id == licor_id)
    )
    licor = res.scalars().one_or_none()
    for dataset in licor.data["datasets"]:
        for key, measurements in dataset.items():
            if key == dataset_id:
                return LICORDataset(key=key, measurements=measurements)
    return
    # raise HTTPException(status_code=404, detail="Dataset not found")


@router.get("", response_model=list[LICORDataRead])
async def get_licors(
    response: Response,
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get all licors"""

    sort = orjson.loads(sort) if sort else []
    range = orjson.loads(range) if range else []
    filter = orjson.loads(filter) if filter else {}

    # Do a query to satisfy total count for "Content-Range" header
    count_query = select(func.count(LICORData.iterator))
    if len(filter):  # Have to filter twice for some reason? SQLModel state?
        for field, value in filter.items():
            if isinstance(value, list):
                count_query = count_query.where(
                    getattr(LICORData, field).in_(value)
                )
            elif field == "id":
                count_query = count_query.where(
                    getattr(LICORData, field) == value
                )
            else:
                count_query = count_query.where(
                    getattr(LICORData, field).like(f"%{value}%")
                )

    # Execute total count query (including filter)
    total_count_query = await session.execute(count_query)
    total_count = total_count_query.scalar_one()

    query = select(LICORData)
    # Order by sort field params ie. ["name","ASC"]
    if len(sort) == 2:
        sort_field, sort_order = sort
        if sort_order == "ASC":
            query = query.order_by(getattr(LICORData, sort_field))
        else:
            query = query.order_by(getattr(LICORData, sort_field).desc())

    # Filter by filter field params ie. {"name":"bar"}
    if len(filter):
        for field, value in filter.items():
            if isinstance(value, list):
                query = query.where(getattr(LICORData, field).in_(value))
            elif field == "id":
                query = query.where(getattr(LICORData, field) == value)
            else:
                query = query.where(
                    getattr(LICORData, field).like(f"%{value}%")
                )

    if len(range) == 2:
        start, end = range
        query = query.offset(start).limit(end - start + 1)
    else:
        start, end = [0, total_count]  # For content-range header

    # Execute query
    results = await session.execute(query)
    licors = results.scalars().all()

    response.headers["Content-Range"] = f"licors {start}-{end}/{total_count}"

    return licors


@router.post("", response_model=LICORDataRead)
async def create_licor(
    licor: LICORDataCreate,
    session: AsyncSession = Depends(get_session),
) -> LICORDataRead:
    """Creates a licor record"""
    # print(licor)

    ####

    """Creates a sensor from one or many GPX files"""

    # Read raw file
    rawdata = decode_base64(
        value=licor.data,
        allowed_types=["data:application/json;base64"],
    )

    serialised_json = orjson.loads(rawdata)

    # Convert integer timestamp to datetime
    converted_date = datetime.datetime.fromtimestamp(serialised_json["date"])
    obj = LICORData(
        name=serialised_json["name"],
        description=serialised_json["remark"],
        recorded_at=converted_date,
        data=orjson.loads(rawdata),
    )

    session.add(obj)
    await session.commit()
    await session.refresh(obj)

    return obj


@router.put("/{licor_id}", response_model=LICORDataRead)
async def update_licor(
    licor_id: UUID,
    licor_update: LICORDataUpdate,
    session: AsyncSession = Depends(get_session),
) -> LICORDataRead:
    res = await session.execute(
        select(LICORData).where(LICORData.id == licor_id)
    )
    licor_db = res.scalars().one()
    licor_data = licor_update.dict(exclude_unset=True)

    if not licor_db:
        raise HTTPException(status_code=404, detail="LICORData not found")

    # Update the fields from the request
    for field, value in licor_data.items():
        print(f"Updating: {field}, {value}")
        setattr(licor_db, field, value)

    session.add(licor_db)
    await session.commit()
    await session.refresh(licor_db)

    return licor_db


@router.delete("/{licor_id}")
async def delete_licor(
    licor_id: UUID,
    session: AsyncSession = Depends(get_session),
    filter: dict[str, str] | None = None,
) -> None:
    """Delete a licor record by id"""
    res = await session.execute(
        select(LICORData).where(LICORData.id == licor_id)
    )
    licor = res.scalars().one_or_none()

    if licor:
        await session.delete(licor)
        await session.commit()
