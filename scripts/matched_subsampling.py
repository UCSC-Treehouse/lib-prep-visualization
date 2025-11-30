from pydantic import BaseModel, field_validator
from pathlib import Path

class MSConfig(BaseModel):
    """
    Matched Sampleing input json config
    """

    out_dir_name: str
    sample_subset: str
    compendia_list: list[str]

    @field_validator("out_dir_name")
    def validate_out_dir_name(cls, v):
        if not v:
            raise ValueError("out_dir_name must be a non-empty string")
        return v
    
    def validate_compendia_list(self, base_path: Path) -> bool:
        for compendia_id in self.compendia_list:
            dir_path = base_path / compendia_id
            if not dir_path.exists() and dir_path.is_dir():
                return False
        return True


def main():
    pass


if __name__ == "__main__":
    main()