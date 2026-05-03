import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_id: str = os.environ["GITHUB_APP_ID"]
    private_key: str = os.environ["GITHUB_PRIVATE_KEY"].replace("\\n", "\n")
    webhook_secret: str = os.environ["GITHUB_WEBHOOK_SECRET"]


settings = Settings()
