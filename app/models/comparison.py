from typing import List, Optional
from pydantic import BaseModel, Field


class ElectricalSpecs(BaseModel):
    power_watts: Optional[str] = None
    voltage_switching: Optional[str] = None
    voltage_breakdown: Optional[str] = None
    current_switching: Optional[str] = None
    current_carry: Optional[str] = None
    resistance_contact: Optional[str] = None
    resistance_insulation: Optional[str] = None
    capacitance: Optional[str] = None
    temperature_operating: Optional[str] = None
    temperature_storage: Optional[str] = None


class MagneticSpecs(BaseModel):
    pull_in_range: Optional[str] = None
    test_coil: Optional[str] = None


class PhysicalSpecs(BaseModel):
    volume: Optional[str] = None
    contact_material: Optional[str] = None
    operate_time: Optional[str] = None
    release_time: Optional[str] = None


class ModelSpecs(BaseModel):
    model: str = Field(..., description="Model identifier")
    features: List[str] = Field(default_factory=list)
    advantages: List[str] = Field(default_factory=list)
    electrical: ElectricalSpecs = Field(default_factory=ElectricalSpecs)
    magnetic: MagneticSpecs = Field(default_factory=MagneticSpecs)
    physical: PhysicalSpecs = Field(default_factory=PhysicalSpecs)
    notes: List[str] = Field(default_factory=list)


class KeyDifferences(BaseModel):
    power: Optional[str] = None
    voltage: Optional[str] = None
    current: Optional[str] = None
    size: Optional[str] = None
    temperature: Optional[str] = None
    other: List[str] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    models: List[ModelSpecs] = Field(
        ...,
        description="Models being compared"
    )
    comparison_type: str = Field(
        ...,
        description=(
            "Type of comparison: full, electrical, magnetic, physical, "
            "or features"
        )
    )
    key_differences: Optional[KeyDifferences] = Field(
        default_factory=KeyDifferences
    )