from pydantic import BaseModel, field_validator
from typing import Any

class VolumeSpec(BaseModel):
    name: str
    path: str
    mode: str

    @field_validator("mode")
    @classmethod
    def valid_mode(cls, v: str) -> str:
        if not v.startswith("0") or not all(c in "01234567" for c in v[1:]):
            raise ValueError(f"invalid octal mode: {v}")
        return v


class ServiceManifest(BaseModel):
    service: str
    uid: int
    user: str
    volumes: list[VolumeSpec]
    read_access: list[str] = []

    @field_validator("read_access")
    @classmethod
    def no_self_reference(cls, v: list[str], info: Any) -> list[str]:
        # Access the 'service' field from the validation context
        if "service" in info.data and info.data["service"] in v:
            raise ValueError("service cannot read its own access")
        return v
