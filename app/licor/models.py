from sqlmodel import SQLModel, Field, UniqueConstraint, Relationship
from uuid import uuid4, UUID
from typing import Any
import datetime
from sqlalchemy import JSON, Column
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.sites.models import Site


class LICORDataBase(SQLModel):
    name: str = Field(default=None, index=True)
    description: str | None = Field(default=None, nullable=True, index=True)
    recorded_at: datetime.datetime = Field(
        title="The datetime in UTC that the record taken by the LICOR",
        nullable=False,
        index=True,
    )
    site_id: UUID | None = Field(
        default=None,
        foreign_key="site.id",
        index=True,
        nullable=True,
    )


class LICORData(LICORDataBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    iterator: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    id: UUID = Field(
        default_factory=uuid4,
        index=True,
        nullable=False,
    )
    created_at: datetime.datetime = Field(
        title="The datetime in UTC that the record was added to the database",
        default_factory=datetime.datetime.now,
        nullable=False,
        index=True,
    )
    data: dict = Field(default={}, sa_column=Column(JSON))
    site: "Site" = Relationship(
        back_populates="licordata", sa_relationship_kwargs={"lazy": "selectin"}
    )


class LICORDataRead(LICORDataBase):
    id: UUID
    created_at: datetime.datetime


class LICORDataReadWithMeasurements(LICORDataRead):
    measurements: list[dict]


class LICORDataCreate(SQLModel):
    data: str  # Base64 encoded string


class LICORDataUpdate(LICORDataBase):
    pass


class LICORDataset(SQLModel):
    key: str
    measurements: dict[str, Any]
