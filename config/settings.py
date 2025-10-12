"""Application settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    app_env: str = "dev"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Database (Sprint 9: PostgreSQL migration)
    DATABASE_URL: str = "postgresql://bookkeeper:bookkeeper_dev_pass@localhost:5432/aibookkeeper"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Redis & Queue (Sprint 4)
    REDIS_URL: str = "redis://localhost:6379/0"
    QUEUE_CONCURRENCY: int = 4
    
    # ML Model (Sprint 4/5)
    ML_MODEL_PATH: str = "models/classifier_open.pkl"
    ML_CONFIDENCE_THRESHOLD: float = 0.85
    
    # OpenAI/LLM
    OPENAI_API_KEY: str = ""
    llm_model: str = "gpt-4"
    confidence_threshold: float = 0.85
    
    # OCR & Document Processing (Sprint 6)
    LLM_VALIDATION_ENABLED: bool = False
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""  # Falls back to OPENAI_API_KEY
    VENDOR_MIN_CONF: float = 0.80
    AMOUNT_MIN_CONF: float = 0.92
    DATE_MIN_CONF: float = 0.85
    CATEGORY_MIN_CONF: float = 0.75
    DOC_TXN_MATCH_MIN: float = 0.88
    OCR_AMOUNT_TOLERANCE: float = 0.05
    OCR_MIN_VENDOR_SIMILARITY: float = 0.70
    
    # Drift Detection & Auto-Retraining (Sprint 7, updated Sprint 9)
    DRIFT_PSI_WARN: float = 0.10
    DRIFT_PSI_ALERT: float = 0.20  # Sprint 9: Updated from 0.25 to 0.20
    DRIFT_ACC_DROP_PCT: float = 3.0
    DRIFT_OCR_CONF_Z: float = 2.0
    DRIFT_MIN_NEW_RECORDS: int = 1000
    DRIFT_MIN_DAYS_SINCE_TRAIN: int = 7
    
    # Retrain Guardrails
    RETRAIN_GUARD_MIN_RECORDS: int = 2000
    RETRAIN_GUARD_MAX_RUNTIME: int = 900
    RETRAIN_GUARD_MIN_IMPROVEMENT: float = -0.01
    RETRAIN_DRY_RUN: bool = False
    RETRAIN_WATCH_INTERVAL: int = 1800
    
    # Model Paths
    MODEL_CANDIDATE: str = "models/candidate_classifier.pkl"
    MODEL_REGISTRY: str = "models/"
    
    # Vector Backend (for vendor knowledge base)
    vector_backend: str = "none"  # Options: "chroma", "none"
    
    # Adaptive Rules (Sprint 8)
    PROMOTE_MIN_OBS: int = 3
    PROMOTE_MIN_CONF: float = 0.85
    PROMOTE_MAX_VAR: float = 0.08
    CONF_DELTA_MIN: float = 0.15
    
    # Decision Blending (Sprint 8)
    W_RULES: float = 0.55
    W_ML: float = 0.35
    W_LLM: float = 0.10
    AUTO_POST_MIN: float = 0.90
    REVIEW_MIN: float = 0.75
    
    # LLM Budget Limits (Sprint 9)
    LLM_GLOBAL_MONTHLY_BUDGET: float = 1000.00
    LLM_TENANT_MONTHLY_BUDGET: float = 50.00
    LLM_CALLS_PER_TXN_ALERT: float = 0.30
    
    # Calibration (Sprint 9)
    CALIBRATION_METHOD: str = "isotonic"  # isotonic|temperature
    CALIBRATION_MIN_SAMPLES: int = 500
    CALIBRATION_ECE_BINS: int = 10
    
    # Cold-Start Enforcement (Sprint 9)
    COLD_START_MIN_LABELS: int = 3
    COLD_START_ENABLED: bool = True
    
    # Reconciliation settings
    recon_date_tolerance_days: int = 3
    
    # Large transaction threshold for auto-review
    large_amount_threshold: float = 5000.0
    
    # Authentication
    secret_key: str = "change-this-to-a-random-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # Legacy aliases for compatibility
    @property
    def database_url(self) -> str:
        return self.DATABASE_URL
    
    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY


settings = Settings()

