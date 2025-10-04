from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application configuration settings"""

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FishNet - AIS Dark Period Detection"
    VERSION: str = "1.0.0"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    DATABASE_URL: str = "sqlite:///./fishnet.db"  # Default to SQLite for demo

    # ML Model Settings
    DARK_PERIOD_THRESHOLD_HOURS: float = 3.0
    MIN_SPEED_THRESHOLD: float = 0.5  # knots
    MAX_SPEED_THRESHOLD: float = 30.0  # knots

    # Risk Scoring Weights
    RISK_WEIGHT_GAP_DURATION: float = 0.3
    RISK_WEIGHT_DISTANCE: float = 0.25
    RISK_WEIGHT_MPA: float = 0.25
    RISK_WEIGHT_NIGHTTIME: float = 0.2

    # File Paths
    DATA_DIR: str = "../datasets"
    MODEL_DIR: str = "./models"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
