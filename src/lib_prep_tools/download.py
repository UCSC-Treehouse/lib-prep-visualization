from pydantic import BaseModel, HttpUrl, field_validator
from typing import List
import re


class CompendiaDownloadConfig(BaseModel):
    compendia_id: str
    expression_url: HttpUrl
    metadata_url: HttpUrl

    @field_validator('compendia_id')
    @classmethod
    def directory_name_safe(cls, v: str) -> str:
        # Only allow alphanumeric, dash, underscore, and dot. Underscore is considered alphanumeric (\w) here. + means one or more, $ means go until the end of the string.
        if not re.match(r'^[\w\-.]+$', v):
            raise ValueError('compendia_id must be directory name safe (alphanumeric, dash, underscore, dot)')
        return v


class DownloadListConfig(BaseModel):
    compendia_downloads: List[CompendiaDownloadConfig]


