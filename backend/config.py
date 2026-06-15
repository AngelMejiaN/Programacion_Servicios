from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    db_server: str
    db_name: str = "TransitProDB"
    db_user: str
    db_password: str
    db_driver:  str = "ODBC Driver 17 for SQL Server"
    secret_key: str = "cambiar-en-produccion-minimo-32-caracteres!!"

    @property
    def database_url(self) -> str:
        driver = self.db_driver.replace(" ", "+")
        return (
            f"mssql+pyodbc://{self.db_user}:{self.db_password}"
            f"@{self.db_server}/{self.db_name}"
            f"?driver={driver}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
