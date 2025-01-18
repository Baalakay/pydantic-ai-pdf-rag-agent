from typing import Dict, Optional
from pydantic import BaseModel, Field, model_validator
from enum import Enum


class UnitType(str, Enum):
    """Enumeration of unit types for standardization."""
    TEMPERATURE = "temperature"
    RESISTANCE = "resistance"
    VOLTAGE = "voltage"
    CURRENT = "current"
    POWER = "power"


class UnitStandard(BaseModel):
    """Standard representation of a unit."""
    symbol: str
    display: str = Field(description="How the unit should be displayed")
    type: Optional[UnitType] = None


class UnitStandardizer:
    """Handles standardization of units across the application."""
    
    # Standard unit mappings
    STANDARD_UNITS: Dict[str, UnitStandard] = {
        # Temperature
        "°C": UnitStandard(
            symbol="°C", 
            display="°C", 
            type=UnitType.TEMPERATURE
        ),
        "°F": UnitStandard(
            symbol="°F", 
            display="°F", 
            type=UnitType.TEMPERATURE
        ),
        # Resistance
        "ohm": UnitStandard(
            symbol="Ω", 
            display="Ω", 
            type=UnitType.RESISTANCE
        ),
        "ohms": UnitStandard(
            symbol="Ω", 
            display="Ω", 
            type=UnitType.RESISTANCE
        ),
        "Ohm": UnitStandard(
            symbol="Ω", 
            display="Ω", 
            type=UnitType.RESISTANCE
        ),
        "Ohms": UnitStandard(
            symbol="Ω", 
            display="Ω", 
            type=UnitType.RESISTANCE
        ),
        # Add more standardizations as needed
    }
    
    @classmethod
    def standardize_unit(cls, unit: Optional[str]) -> Optional[str]:
        """Standardize a unit string to its canonical form."""
        if not unit:
            return None
            
        # Handle temperature units with qualifiers
        if "°" in unit:
            if "°C" in unit:
                return cls.STANDARD_UNITS["°C"].display
            elif "°F" in unit:
                return cls.STANDARD_UNITS["°F"].display
                
        # Handle resistance units
        if any(unit.lower().startswith(ohm) for ohm in ["ohm", "Ohm"]):
            return cls.STANDARD_UNITS["ohm"].display
            
        # If no standardization needed, return as is
        return unit


class TransformedSpecValue(BaseModel):
    """Represents a specification value with standardized unit."""
    raw_unit: Optional[str] = None
    standardized_unit: Optional[str] = None
    value: str
    
    @model_validator(mode='before')
    def standardize_units(cls, data: dict) -> dict:
        """Standardize units before validation."""
        if isinstance(data, dict) and 'raw_unit' in data:
            data['standardized_unit'] = UnitStandardizer.standardize_unit(
                data['raw_unit']
            )
        return data


class SpecTransformer:
    """Handles transformation of specification values."""
    
    @staticmethod
    def transform_spec(
        unit: Optional[str], 
        value: str
    ) -> TransformedSpecValue:
        """Transform a specification value, standardizing its unit."""
        return TransformedSpecValue(
            raw_unit=unit,
            value=value
        ) 