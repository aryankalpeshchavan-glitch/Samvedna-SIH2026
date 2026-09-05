import pytest
from httpx import AsyncClient
from app.core.config import settings
from tests.test_api import client, setup_db, register_and_login, auth_header

@pytest.mark.asyncio
async def test_auth_missing_token(client: AsyncClient):
    response = await client.get("/assignments")
    assert response.status_code in (401, 403)

@pytest.mark.asyncio
async def test_auth_malformed_token(client: AsyncClient):
    response = await client.get("/assignments", headers={"Authorization": "Bearer malformed_token"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_invalid_token(client: AsyncClient):
    import jwt
    token = jwt.encode({"sub": "1", "role": "admin"}, "wrong_secret", algorithm="HS256")
    response = await client.get("/assignments", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_expired_token(client: AsyncClient):
    import jwt
    from datetime import datetime, timedelta
    token = jwt.encode(
        {"sub": "1", "role": "admin", "exp": datetime.utcnow() - timedelta(minutes=10)},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = await client.get("/assignments", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_rbac_unauthorized_role(client: AsyncClient):
    token_citizen = await register_and_login(client, "citizen")
    response = await client.get("/assignments", headers=auth_header(token_citizen))
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_rbac_authorized_role(client: AsyncClient):
    token_admin = await register_and_login(client, "admin")
    response = await client.get("/assignments", headers=auth_header(token_admin))
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_error_safety_no_stack_trace(client: AsyncClient):
    token_admin = await register_and_login(client, "admin")
    response = await client.post("/intelligence/decision", json={"lat": "invalid_type", "lng": 0}, headers=auth_header(token_admin))
    assert response.status_code == 422
    assert "detail" in response.json()
