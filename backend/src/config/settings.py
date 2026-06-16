from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str
    GOOGLE_CLIENT_ID : str
    JWT_SECRET_KEY:str
    JWT_ALGORITHM:str


    class Config:
        env_file =".env"
    

settings = Settings()

