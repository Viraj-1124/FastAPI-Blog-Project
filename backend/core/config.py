import os
from dotenv import load_dotenv

from pathlib import Path
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_TITLE: str = "Blog"
    PROJECT_VERSION: str = "0.1.0"

    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRESS_SERVER: str =  os.getenv("POSTGRES_SERVER","localhost")
    POSTGRESS_PORT: int = os.getenv("POSTGRES_PORT",5432)
    POSTGRESS_DB: str= os.getenv("POSTGRES_DB")
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRESS_SERVER}:{POSTGRESS_PORT}/{POSTGRESS_DB}"

settings = Settings()