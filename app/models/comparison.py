from typing import List, Optional, Dict, Callable
from pydantic import BaseModel, Field

class ElectricalSpecs(BaseModel):
    power_watts: Optional[str] = Field(None, description="Maximum power in watts")
    voltage_switching: Optional[str] = Field(None, description="Maximum switching voltage")
    voltage_breakdown: Optional[str] = Field(None, description="Minimum breakdown voltage")
    current_switching: Optional[str] = Field(None, description="Maximum switching current")
    current_carry: Optional[str] = Field(None, description="Maximum carry current")
    resistance_contact: Optional[str] = Field(None, description="Maximum contact resistance")
    resistance_insulation: Optional[str] = Field(None, description="Minimum insulation resistance")
    capacitance: Optional[str] = Field(None, description="Typical contact capacitance")
    temperature_operating: Optional[str] = Field(None, description="Operating temperature range")
    temperature_storage: Optional[str] = Field(None, description="Storage temperature range")

class MagneticSpecs(BaseModel):
    pull_in_range: Optional[str] = Field(None, description="Pull-in range in ampere turns")
    test_coil: Optional[str] = Field(None, description="Test coil specification")

class PhysicalSpecs(BaseModel):
    volume: Optional[str] = Field(None, description="Nominal capsule volume")
    contact_material: Optional[str] = Field(None, description="Contact material type")
    operate_time: Optional[str] = Field(None, description="Maximum operate time including bounce")
    release_time: Optional[str] = Field(None, description="Maximum release time")

class ModelSpecs(BaseModel):
    model: str = Field(..., description="Model number")
    features: List[str] = Field(default_factory=list, description="Model features")
    advantages: List[str] = Field(default_factory=list, description="Model advantages")
    electrical: ElectricalSpecs = Field(default_factory=ElectricalSpecs, description="Electrical specifications")
    magnetic: MagneticSpecs = Field(default_factory=MagneticSpecs, description="Magnetic specifications")
    physical: PhysicalSpecs = Field(default_factory=PhysicalSpecs, description="Physical specifications")
    notes: List[str] = Field(default_factory=list, description="Important notes")
    diagram_path: Optional[str] = Field(None, description="Path to model diagram")

class KeyDifferences(BaseModel):
    power: Optional[str] = Field(None, description="Power handling difference")
    voltage: Optional[str] = Field(None, description="Voltage rating difference")
    current: Optional[str] = Field(None, description="Current handling difference")
    size: Optional[str] = Field(None, description="Size/volume difference")
    temperature: Optional[str] = Field(None, description="Temperature range difference")
    other: List[str] = Field(default_factory=list, description="Other notable differences")

class ComparisonResult(BaseModel):
    models: List[ModelSpecs] = Field(..., description="List of model specifications to compare")
    comparison_type: str = Field(..., description="Type of comparison: full, electrical, magnetic, physical, or features")
    key_differences: Optional[KeyDifferences] = Field(None, description="Highlighted key differences between models")