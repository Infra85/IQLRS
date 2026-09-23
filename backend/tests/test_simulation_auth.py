"""Exercise the real login, JWT validation, and optional simulation identity."""
from datetime import timedelta
from uuid import uuid4

import pytest
from jose import jwt

from app.core.security import ALGORITHM, create_access_token, hash_password
from app.models import User

CIRCUIT = {"gates": [], "num_qubits": 1, "shots": 64}


def test_login_token_simulates_and_guests_remain_supported(api, sessions):
    client, uid = api
    with sessions() as db:
        db.get(User, uid).password_hash = hash_password("simulation-test-password")
        db.commit()
    client.headers.pop("Authorization")
    assert client.get("/api/dashboard/me").status_code == 401
    guest = client.post("/api/circuits/simulate", json=CIRCUIT)
    assert guest.status_code == 200
    assert guest.json()["simulation_id"] is None
    login = client.post("/api/auth/login", json={
        "email": "integration@example.com", "password": "simulation-test-password",
    })
    assert login.status_code == 200
    client.headers["Authorization"] = "Bearer " + login.json()["access_token"]
    result = client.post("/api/circuits/simulate", json=CIRCUIT)
    assert result.status_code == 200, result.text
    assert result.json()["counts"] == {"0": 64}
    run_path = "/api/circuits/runs/" + result.json()["simulation_id"]
    assert client.get(run_path).status_code == 200
    client.headers.pop("Authorization")
    assert client.get(run_path).status_code == 401


@pytest.mark.parametrize("kind", ["expired", "old-secret", "missing-user", "unverified", "malformed"])
def test_rejected_tokens_are_not_treated_as_guests(api, sessions, kind):
    client, uid = api
    if kind == "expired":
        token = create_access_token({"sub": str(uid)}, expires_delta=timedelta(minutes=-1))
    elif kind == "old-secret":
        token = jwt.encode({"sub": str(uid)}, "different-test-secret", algorithm=ALGORITHM)
    elif kind == "missing-user":
        token = create_access_token({"sub": str(uuid4())})
    elif kind == "unverified":
        with sessions() as db:
            db.get(User, uid).email_verified = False
            db.commit()
        token = create_access_token({"sub": str(uid)})
    else:
        token = "invalid"
    response = client.post("/api/circuits/simulate", json=CIRCUIT,
                           headers={"Authorization": "Bearer " + token})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
    assert response.headers["www-authenticate"] == "Bearer"
