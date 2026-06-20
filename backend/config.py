from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Modo demo ─────────────────────────────────────────────────────────────
    # true  → SQLite local (demo.db), sin SQL Server
    # false → SQL Server (requiere DB_SERVER, DB_USER, DB_PASSWORD)
    demo_mode: bool = False

    # ── Base de datos (SQL Server) ────────────────────────────────────────────
    db_server:   str = ""
    db_name:     str = "TransitProDB"
    db_user:     str = ""
    db_password: str = ""
    db_driver:   str = "ODBC Driver 17 for SQL Server"

    # ── Seguridad ─────────────────────────────────────────────────────────────
    secret_key: str = "cambiar-en-produccion-minimo-32-caracteres!!"

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Lista de orígenes separada por comas, o "*" para todos.
    cors_origins: str = "*"

    # ── Bot ───────────────────────────────────────────────────────────────────
    bot_token: str = ""
    timezone:  str = "America/Lima"
    hora_notif_conductores:  int = 20
    hora_notif_programador:  int = 7

    @property
    def database_url(self) -> str:
        if self.demo_mode:
            return "sqlite:///./demo.db"
        if not self.db_server or not self.db_user:
            raise ValueError(
                "DB_SERVER y DB_USER son obligatorios cuando DEMO_MODE=false. "
                "Para correr sin SQL Server usa DEMO_MODE=true."
            )
        driver = self.db_driver.replace(" ", "+")
        return (
            f"mssql+pyodbc://{self.db_user}:{self.db_password}"
            f"@{self.db_server}/{self.db_name}"
            f"?driver={driver}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
