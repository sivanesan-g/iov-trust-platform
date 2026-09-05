import datetime as dt

import jwt

from backend.config import JWT_ALGORITHM, JWT_AUDIENCE, JWT_ISSUER, JWT_SECRET


def encode_vehicle_token(vehicle_id: str, device_id: str, expires_in_seconds: int = 3600):
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": vehicle_id,
        "device_id": device_id,
        "scope": "telemetry:write",
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(seconds=expires_in_seconds)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_vehicle_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], audience=JWT_AUDIENCE, issuer=JWT_ISSUER)


def verify_vehicle_identity(claims: dict, vehicle_id: str):
    if not claims:
        return False, "missing_token_claims"
    if claims.get("sub") != vehicle_id:
        return False, "vehicle_identity_mismatch"
    if claims.get("scope") != "telemetry:write":
        return False, "invalid_scope"
    return True, "token_valid"
