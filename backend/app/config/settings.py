"""FROGÉ HQ configuration — all values from environment/settings. Never hard-code a model."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "FROGÉ HQ"
    env: str = "development"

    # Database (SQLite first, PostgreSQL-ready)
    database_url: str = "sqlite+aiosqlite:///./froge_hq.db"

    # Resource Governor limits (configurable, low-spec friendly)
    max_active_agents: int = 5
    max_browser_instances: int = 1
    max_queue_size: int = 50

    # Model Gateway — the Arena AI Agent provider is supplied via config only.
    # No model name is hard-coded anywhere in the codebase.
    model_provider: str = "arena"          # provider identifier from env
    model_name: str = ""                    # selected Arena AI Agent model, from env
    model_api_base: str = ""                # provider endpoint, from env
    model_api_key: str = ""                 # provider key, from env

    # Owner sign-in (empty = open dev mode, no login required)
    owner_email: str = ""
    owner_password: str = ""
    auth_secret: str = ""

    # Static frontend (production: serve the Vite build from FastAPI)
    frontend_dist: str = "../frontend/dist"

    # Workspace sandbox root for tool execution
    workspace_root: str = "./workspace_sandbox"

    # CORS — comma-separated allowed origins. Empty = permissive dev ("*").
    # Production: set to your live URL, e.g. "https://froge-hq.onrender.com"
    cors_origins: str = ""

    # Auth rate limiting (login/signup attempts per IP per window)
    auth_rate_limit: int = 10          # max attempts
    auth_rate_window_s: int = 300      # per 5-minute window

    class Config:
        env_prefix = "FROGE_"
        env_file = ".env"


settings = Settings()
