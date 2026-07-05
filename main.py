from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

app = FastAPI()

# -------------------------------
# Allowed CORS Origins
# -------------------------------
# Add BOTH:
# 1. Assigned origin
# 2. Exam page origin (change if your exam page uses another origin)
origins = [
    "https://app-is3l09.example.com",
    "https://examly.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Rate Limiter Middleware
# -------------------------------
RATE_LIMIT = 14
WINDOW = 10

client_buckets = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        client = request.headers.get("X-Client-Id", "anonymous")

        now = time.time()

        timestamps = client_buckets.get(client, [])

        timestamps = [t for t in timestamps if now - t < WINDOW]

        if len(timestamps) >= RATE_LIMIT:
            retry_after = max(1, int(WINDOW - (now - timestamps[0])))

            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )

        timestamps.append(now)
        client_buckets[client] = timestamps

        return await call_next(request)


# -------------------------------
# Request Context Middleware
# -------------------------------
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response


# Order:
# Request Context -> Rate Limit -> Route
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "YOUR_EMAIL@example.com",
        "request_id": request.state.request_id,
    }