from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME : str = 'APIRESTFUL E-COMMERCE'
    PROJECT_VERSION : str = '1.0'
    DATABASE_URL : str
    
    class Config: 
        env_file = '.env'
        
settings = Settings()