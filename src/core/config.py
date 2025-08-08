from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME : str = 'APIRESTFUL E-COMMERCE'
    PROJECT_VERSION : str = '1.0'
    DATABASE_URL : str
    
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    ISSUER: str
    AUDIENCE: str

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
        
settings = Settings()