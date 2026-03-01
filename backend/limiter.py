from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_rate_limit_key(request: Request) -> str:
    """Use the first 32 chars of the Bearer token as the bucket key for
    authenticated routes, and the client IP for unauthenticated ones."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        if token:
            return token[:32]
    return get_remote_address(request)


limiter = Limiter(key_func=get_rate_limit_key)
