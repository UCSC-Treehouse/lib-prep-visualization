from pydantic import BaseModel, field_validator
import re

class CompendiaSource(BaseModel):
    """
    Model for a single compendia entry in the process_data config.
    """
    
    compendia_id: str
    lib_prep_type: str

    @field_validator("compendia_id")
    @classmethod
    def directory_name_safe(cls, v: str) -> str:
        # Make sure that the compendia_id is directory name safe. Precaution to make sure that no funny business happens with directory names.
        if not re.match(r"^[\w\-.]+$", v):
            raise ValueError(
                "compendia_id must be directory name safe (alphanumeric, dash, underscore, dot)"
            )
        return v
    
class CompendiaListConfig(BaseModel):
    """
    Top-level model for the process_data JSON config.
    Attributes:
        compendia_list (list[CompendiaSource]): List of compendia sources to merge.
        ...More attributes on how to merge the data... (TBD)
    """
    
    compendia_list: list[CompendiaSource]