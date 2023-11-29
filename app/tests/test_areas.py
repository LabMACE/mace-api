# from fastapi.testclient import TestClient
# from sqlmodel import Session, SQLModel, create_engine
# from app.db import init_db
# from app.main import app
# import pytest
# from uuid import UUID
# from httpx import AsyncClient
# from sqlalchemy.ext.asyncio import AsyncSession


def test_pass():
    assert True


# @pytest.mark.asyncio
# async def test_create_area(
#     async_client: AsyncClient,
#     async_session: AsyncSession,
# ):
#     response = await async_client.post(
#         "/areas",
#         json={"name": "Binntal", "description": "Binntal area"},
#     )
#     print(response.__dict__)
#     print(response.content)
#     data = response.json()

#     assert response.status_code == 200

#     assert data["name"] == "Binntal"
#     assert data["description"] == "Binntal area"
#     assert UUID(data["id"], version=4)
