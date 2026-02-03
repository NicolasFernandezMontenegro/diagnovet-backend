from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone


class Patient(BaseModel):
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[str] = None
    sex: Optional[str] = None


class Owner(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None


class Veterinarian(BaseModel):
    name: Optional[str] = None
    clinic: Optional[str] = None


class Report(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    patient: Patient
    owner: Owner
    veterinarian: Veterinarian

    diagnosis: Optional[str] = None
    recommendations: Optional[str] = None

    image_urls: List[str] = Field(default_factory=list)

    created_at: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc)
)