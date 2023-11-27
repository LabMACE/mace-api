from sqlmodel import SQLModel, Field, Column, UniqueConstraint, Relationship
from geoalchemy2 import Geometry, WKBElement
from uuid import uuid4, UUID
from typing import Any
import shapely
from pydantic import validator, root_validator
from typing import TYPE_CHECKING
from typing import List
import datetime

if TYPE_CHECKING:
    from app.fieldcampaigns.models import FieldCampaign


class SiteBase(SQLModel):
    name: str = Field(default=None, index=True)
    description: str
    field_campaign_id: UUID = Field(
        default=None, foreign_key="fieldcampaign.id", index=True
    )


class Site(SiteBase, table=True):
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
    geom: Any = Field(sa_column=Column(Geometry("POINTZ", srid=4326)))

    field_campaign: "FieldCampaign" = Relationship(
        back_populates="sites", sa_relationship_kwargs={"lazy": "selectin"}
    )


class SiteRead(SiteBase):
    id: UUID  # We use the UUID as the return ID
    geom: Any
    latitude: float
    longitude: float
    elevation: float

    @root_validator
    def convert_wkb_to_lat_lon(cls, values: dict) -> dict:
        """Form the geometry from the latitude and longitude and elevation"""
        if isinstance(values["geom"], WKBElement):
            if values["geom"] is not None:
                shapely_obj = shapely.wkb.loads(str(values["geom"]))
                if shapely_obj is not None:
                    mapping = shapely.geometry.mapping(shapely_obj)

                    values["latitude"] = mapping["coordinates"][0]
                    values["longitude"] = mapping["coordinates"][1]
                    values["elevation"] = mapping["coordinates"][2]
                    values["geom"] = mapping
        elif isinstance(values["geom"], dict):
            if values["geom"] is not None:
                values["latitude"] = values["geom"]["coordinates"][0]
                values["longitude"] = values["geom"]["coordinates"][1]
                values["elevation"] = values["geom"]["coordinates"][2]
                values["geom"] = values["geom"]
        else:
            values["latitude"] = None
            values["longitude"] = None
            values["elevation"] = None

        return values


class SiteCreate(SiteBase):
    latitude: float
    longitude: float
    elevation: float
    geom: Any | None = None

    @root_validator(pre=True)
    def convert_lat_lon_to_wkt(cls, values: dict) -> dict:
        """Form the geometry from the latitude and longitude and elevation"""

        if "latitude" in values and "longitude" in values:
            values["geom"] = "POINT({lat} {lon} {elevation})".format(
                lat=values["latitude"],
                lon=values["longitude"],
                elevation=values["elevation"],
            )

        return values


class SiteUpdate(SiteBase):
    pass
