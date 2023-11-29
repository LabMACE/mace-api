from fastapi import FastAPI, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import config
from app.db import get_session, AsyncSession
from app.sites.views import router as sites_router
from app.subsites.views import router as subsites_router
from app.fieldcampaigns.views import router as field_campaigns_router
from pydantic import BaseModel

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


@app.get(
    "/healthz",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def get_health(
    session: AsyncSession = Depends(get_session),
) -> HealthCheck:
    """
    Endpoint to perform a healthcheck on for kubenernetes liveness and
    readiness probes.
    """
    # Check DB connection
    try:
        await session.execute("SELECT 1")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Error: {e}")

    return HealthCheck(status="OK")


app.include_router(
    sites_router,
    prefix=f"{config.API_V1_PREFIX}/sites",
    tags=["sites"],
)
app.include_router(
    subsites_router,
    prefix=f"{config.API_V1_PREFIX}/subsites",
    tags=["subsites"],
)

app.include_router(
    field_campaigns_router,
    prefix=f"{config.API_V1_PREFIX}/fieldcampaigns",
    tags=["fieldcampaigns"],
)
