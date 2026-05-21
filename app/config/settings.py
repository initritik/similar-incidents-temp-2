from dotenv import load_dotenv
from pydantic import BaseModel

import os

load_dotenv()


class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "Similar Incidents AI")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.2.0")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "servicenow_incidents")

    RESULT_FIELDS: str = os.getenv(
        "RESULT_FIELDS",
        "number,short_description,description,assignment_group,"
        "priority,category,resolution_notes,servicenow_link,"
        "azure_devops_link,datafix_code,similarity_score",
    )

    @property
    def result_fields_set(self) -> set:
        return {f.strip() for f in self.RESULT_FIELDS.split(",") if f.strip()}


settings = Settings()