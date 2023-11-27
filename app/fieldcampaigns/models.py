from sqlmodel import SQLModel, Field, Column, UniqueConstraint, Relationship
from uuid import uuid4, UUID
from typing import Any
from typing import TYPE_CHECKING
import datetime
from app.sites.models import Site


class FieldCampaignBase(SQLModel):
    name: str = Field(default=None, index=True)
    description: str


class FieldCampaign(FieldCampaignBase, table=True):
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
        default=datetime.datetime.utcnow,
        nullable=False,
        index=True,
    )

    sites: list["Site"] = Relationship(
        back_populates="field_campaign",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class FieldCampaignRead(FieldCampaignBase):
    id: UUID
    sites: list["Site"] = []


class FieldCampaignCreate(FieldCampaignBase):
    pass


class FieldCampaignUpdate(FieldCampaignBase):
    pass
