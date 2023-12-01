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
    from app.subsites.models import SubSite
    from app.fieldcampaigns.models import FieldCampaign
    from app.licor.models import LICORData


class SiteBase(SQLModel):
    name: str = Field(default=None, index=True)
    description: str | None = Field(default=None, nullable=True, index=True)
    field_campaign_id: UUID = Field(
        default=None, foreign_key="fieldcampaign.id", index=True
    )
    location: str = Field(default=None, index=True)


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
        title="The datetime in UTC that the record was added to the database",
        default_factory=datetime.datetime.now,
        nullable=False,
        index=True,
    )
    geom: Any | None = Field(sa_column=Column(Geometry("POINTZ", srid=4326)))

    field_campaign: "FieldCampaign" = Relationship(
        back_populates="sites", sa_relationship_kwargs={"lazy": "selectin"}
    )

    subsites: List["SubSite"] = Relationship(
        back_populates="site", sa_relationship_kwargs={"lazy": "selectin"}
    )

    licordata: List["LICORData"] = Relationship(
        back_populates="site", sa_relationship_kwargs={"lazy": "selectin"}
    )


class SiteRead(SiteBase):
    id: UUID  # We use the UUID as the return ID
    geom: Any
    created_at: datetime.datetime
    latitude: float | None = 0
    longitude: float | None = 0
    elevation: float | None = 0

    field_campaign: Any

    @root_validator
    def convert_wkb_to_lat_lon(cls, values: dict) -> dict:
        """Form the geometry from the latitude and longitude and elevation"""

        if isinstance(values["geom"], WKBElement):
            if values["geom"] is not None:
                shapely_obj = shapely.wkb.loads(str(values["geom"]))
                if shapely_obj is not None:
                    values["geom"] = shapely.geometry.mapping(shapely_obj)
                    (
                        values["latitude"],
                        values["longitude"],
                        values["elevation"],
                    ) = values["geom"]["coordinates"]
        else:
            values["latitude"] = None
            values["longitude"] = None
            values["elevation"] = None
            values["geom"] = None

        return values


class SiteCreate(SiteBase):
    latitude: float | None
    longitude: float | None
    elevation: float | None
    geom: Any | None

    @root_validator(pre=True)
    def convert_lat_lon_to_wkt(cls, values: dict) -> dict:
        """Form the geometry from the latitude and longitude and elevation"""

        # Only save geometry if we have both latitude and longitude
        if ("latitude" in values and "longitude" in values) and (
            values["latitude"] is not None and values["longitude"] is not None
        ):
            values["geom"] = "POINT({lat} {lon} {elevation})".format(
                lat=values["latitude"],
                lon=values["longitude"],
                # Elevation can be None, if so then set to 0
                elevation=values["elevation"]
                if values["elevation"] is not None
                else 0,
            )

        return values


class SiteUpdate(SiteBase):
    latitude: float | None
    longitude: float | None
    elevation: float | None
    geom: Any | None

    @root_validator(pre=True)
    def convert_lat_lon_to_wkt(cls, values: dict) -> dict:
        """Form the geometry from the latitude and longitude and elevation"""

        # Only save geometry if we have both latitude and longitude
        if ("latitude" in values and "longitude" in values) and (
            values["latitude"] is not None and values["longitude"] is not None
        ):
            values["geom"] = "POINT({lat} {lon} {elevation})".format(
                lat=values["latitude"],
                lon=values["longitude"],
                # Elevation can be None, if so then set to 0
                elevation=values["elevation"]
                if values["elevation"] is not None
                else 0,
            )

        return values
