from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  s3_endpoint: str
  aws_access_key_id: str
  aws_secret_access_key: str
  bucket_name: str

  model_config = SettingsConfigDict(
      env_file=".env", env_file_encoding="utf-8", extra="ignore"
  )


settings = Settings()