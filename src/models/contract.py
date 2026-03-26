from pydantic import BaseModel
from typing import List

class ContractViolation(BaseModel):
    service: str
    field: str
    message: str

class ValidationResult(BaseModel):
    valid: bool
    errors: List[ContractViolation]

class ComposeDef(BaseModel):
    name: str
    image: str
    user: str
    volumes: List[str]
