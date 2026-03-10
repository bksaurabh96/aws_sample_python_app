import hmac
import os
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class Item(BaseModel):
    id: str
    name: str


app = FastAPI(
    title="AWS Sample Python App",
    version="0.1.0",
    redoc_url=None,
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description="Use the **Authorize** button above and enter your API token (e.g. `token005`) to call protected endpoints.",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "Bearer",
            "description": "Enter your API token",
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Authorization"],
)


security = HTTPBearer(auto_error=True, scheme_name="BearerAuth")


def get_api_token() -> str:
    token = os.getenv("API_TOKEN")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is not properly configured.",
        )
    return token


def authenticate(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:
    expected_token = get_api_token()
    if credentials.scheme.lower() != "bearer" or not hmac.compare_digest(
        credentials.credentials, expected_token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token.",
        )


@app.get("/health", response_model=HealthResponse)
def health_check(auth: None = Depends(authenticate)) -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/items", response_model=List[Item])
def get_items(auth: None = Depends(authenticate)) -> List[Item]:
    items: List[Item] = [
        Item(id="1", name="Item One"),
        Item(id="2", name="Item Two"),
    ]
    return items


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Sample Python App</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f0f12;
            --surface: #18181c;
            --border: #2a2a30;
            --text: #e4e4e7;
            --muted: #71717a;
            --accent: #22d3ee;
            --accent-dim: rgba(34, 211, 238, 0.15);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            background-image:
                radial-gradient(ellipse 80% 50% at 50% -20%, var(--accent-dim), transparent),
                radial-gradient(ellipse 60% 40% at 100% 100%, rgba(34, 211, 238, 0.06), transparent);
        }
        .container { max-width: 520px; width: 100%; }
        h1 { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.25rem; }
        .subtitle { color: var(--muted); font-size: 0.95rem; margin-bottom: 2rem; }
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 0.75rem;
        }
        .card h2 {
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin-bottom: 0.75rem;
        }
        .endpoint {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.6rem 0;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
        }
        .endpoint:last-child { border-bottom: none; }
        .method { font-weight: 600; color: var(--accent); font-size: 0.75rem; min-width: 3rem; }
        .path { font-family: ui-monospace, monospace; }
        .auth { font-size: 0.7rem; color: var(--muted); }
        .links { margin-top: 2rem; display: flex; gap: 1rem; flex-wrap: wrap; }
        .links a { color: var(--accent); text-decoration: none; font-size: 0.9rem; font-weight: 500; }
        .links a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>AWS Sample Python App</h1>
        <p class="subtitle">FastAPI · Docker · GitHub Actions · ECS Fargate</p>
        <div class="card">
            <h2>API Endpoints</h2>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/health</span>
                <span class="auth">Bearer token</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/items</span>
                <span class="auth">Bearer token</span>
            </div>
        </div>
        <div class="links">
            <a href="/docs">OpenAPI docs</a>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html)
