import os

class Config:
    # Database
    DB_USER     = os.environ.get("DB_USER",     "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
    DB_HOST     = os.environ.get("DB_HOST",     "localhost")
    DB_PORT     = os.environ.get("DB_PORT",     "5432")
    DB_NAME     = os.environ.get("DB_NAME",     "blacklist_db")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT — token estático para toda la aplicación
    # En producción este valor viene de una variable de entorno
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret-key-change-in-prod")
    STATIC_TOKEN   = os.environ.get("STATIC_TOKEN",   "my-static-bearer-token")
