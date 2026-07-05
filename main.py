from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

# ---------------------------------
# CORS
# ---------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-is3l09.example.com",
        "https://examly.io",
        "https://app.examly.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------
# Rate Limit Configuration
# ---------------------------------
RATE_LIMIT = 14
WINDOW = 10  # seconds

client_buckets = {}


# ---------------------------------
# Request Context Middleware
# ---------------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    # Echo the request ID back
    response.headers["X-Request-ID"] = request_id

    return response


# ---------------------------------
# Rate Limiting Middleware
# ---------------------------------
@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    timestamps = client_buckets.get(client_id, [])
    timestamps = [t for t in timestamps if now - t < WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        retry_after = max(1, int(WINDOW - (now - timestamps[0])))

        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(retry_after)},
        )

    timestamps.append(now)
    client_buckets[client_id] = timestamps

    return await call_next(request)


# ---------------------------------
# Root Endpoint
# ---------------------------------
@app.get("/")
async def root():
    return {"status": "ok"}


# ---------------------------------
# Ping Endpoint
# ---------------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "24f3005089@ds.study.iitm.ac.in",
        "request_id": request.state.request_id,
    }