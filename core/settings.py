from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: SecretStr
    redis_ip: SecretStr
    
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings(_env_file='secret_data.env', _env_file_encoding='utf-8')
