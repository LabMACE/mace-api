from sqlmodel import SQLModel, Field, Column, UniqueConstraint, Relationship
from geoalchemy2 import Geometry, WKBElement
from uuid import uuid4, UUID
from typing import Any
import shapely
from pydantic import validator, root_validator
from typing import TYPE_CHECKING
import datetime
from sqlalchemy import JSON, Column

if TYPE_CHECKING:
    from app.sites.models import Site


class TemperatureMeasurementBase(SQLModel):
    measurement_celsius: float = Field(
        title="The measurement", default=None, index=True
    )
    thermometer_characteristic: str = Field(
        title="The thermometer characteristic, such as black or white",
        default=None,
        index=True,
    )

    type: str = Field(
        title="The type of measurement, such as air or soil",
        default=None,
        index=True,
    )
    depth_from_surface_cm: str = Field(
        title="The depth in centimeters from the surface such as 2 to 5 cm",
        default=None,
        index=True,
    )


class LuminosityMeasurementBase(SQLModel):
    measurement_lux: float = Field(title="The measurement", default=None)


class SubSiteBase(SQLModel):
    name: str = Field(default=None, index=True)
    description: str
    site_id: UUID = Field(foreign_key="site.id", index=True)
    location: str = Field(default=None, index=True)
    recorded_at: datetime.datetime = Field(
        title="The time recorded by the scientist",
        nullable=False,
        index=True,
    )

    temperatures: list[TemperatureMeasurementBase] | None = Field(
        default=[], sa_column=Column(JSON)
    )
    luminosities: list[LuminosityMeasurementBase] | None = Field(
        default=[], sa_column=Column(JSON)
    )

    class Config:
        arbitrary_types_allowed = True


class SubSite(SubSiteBase, table=True):
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

    geom: Any = Field(sa_column=Column(Geometry("POINTZ", srid=4326)))

    site: "Site" = Relationship(
        back_populates="subsites", sa_relationship_kwargs={"lazy": "selectin"}
    )


class SubSiteRead(SubSiteBase):
    id: UUID  # We use the UUID as the return ID
    geom: Any
    created_at: datetime.datetime
    recorded_at: datetime.datetime
    latitude: float | None
    longitude: float | None
    elevation: float | None

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


class SubSiteCreate(SubSiteBase):
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

    @validator("recorded_at")
    def remove_timezone(cls, v):
        return v.replace(tzinfo=None)


class SubSiteUpdate(SubSiteBase):
    pass