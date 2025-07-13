from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME : str = 'APIRESTFUL E-COMMERCE'
    PROJECT_VERSION : str = '1.0'
    DATABASE_URL : str
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
        
settings = Settings()