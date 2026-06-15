"""
Configuración del bot de Telegram.
Las variables se leen desde el archivo .env ubicado en la raíz del proyecto
(el mismo que usa el backend FastAPI).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Telegram ────────────────────────────────────────────────────────────
    bot_token: str = ""                   # BOT_TOKEN en .env

    # ── Base de datos (mismas vars que el backend) ───────────────────────────
    db_server:   str = "localhost"
    db_name:     str = "TransitPro"
    db_user:     str = ""
    db_password: str = ""
    db_driver:   str = "ODBC Driver 17 for SQL Server"

    # ── Zona horaria (Lima, Perú) ────────────────────────────────────────────
    timezone: str = "America/Lima"

    # ── Hora de las notificaciones automáticas ───────────────────────────────
    hora_notif_conductores: int = 20   # 8 PM → servicios del día siguiente
    hora_notif_programador: int = 7    # 7 AM → servicios sin conductor

    @property
    def database_url(self) -> str:
        driver_encoded = self.db_driver.replace(" ", "+")
        return (
            f"mssql+pyodbc://{self.db_user}:{self.db_password}"
            f"@{self.db_server}/{self.db_name}"
            f"?driver={driver_encoded}"
        )


settings = BotSettings()
