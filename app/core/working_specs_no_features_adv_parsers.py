from typing import List, Optional, Dict, Any, Union
import re
from app.models.pdf import (
    SpecValue,
    ElectricalSpecs,
    MagneticSpecs,
    PhysicalSpecs,
)


class PDFSectionParser:
    """Parser for extracting structured content from PDF sections."""
    
    @staticmethod
    def _extract_value_unit(value_str: str) -> Optional[SpecValue]:
        """Extract numeric value and optional unit from a string."""
        if not value_str:
            return None
            
        # Handle ranges like "10 to 20" or "10-20"
        range_pattern = r'([\d.]+)\s*(?:to|-)\s*([\d.]+)\s*([A-Za-z/°]+)?'
        range_match = re.search(range_pattern, value_str)
        if range_match:
            value = float(range_match.group(2))
            unit = range_match.group(3)
            return SpecValue(value=value, unit=unit)
            
        # Handle simple numeric values
        value_pattern = r'([\d.]+)\s*([A-Za-z/°]+)?'
        value_match = re.search(value_pattern, value_str)
        if value_match:
            value = float(value_match.group(1))
            unit = value_match.group(2)
            return SpecValue(value=value, unit=unit)
            
        return None

    @classmethod
    def parse_section(
        cls, 
        lines: List[str], 
        section_type: str
    ) -> Union[Dict[str, Any], List[str], str]:
        """Parse any section based on its structure and content."""
        if section_type == 'electrical':
            return cls.parse_electrical(lines).model_dump()
        elif section_type == 'magnetic':
            return cls.parse_magnetic(lines).model_dump()
        elif section_type == 'physical':
            return cls.parse_physical(lines).model_dump()
        elif section_type in ['features', 'advantages']:
            return cls.parse_features_advantages(lines)
        else:
            return cls.parse_notes(lines)

    @classmethod
    def _parse_spec_lines(
        cls,
        lines: List[str]
    ) -> Dict[str, Dict[str, SpecValue]]:
        """Parse lines into a dictionary of specifications."""
        specs: Dict[str, Dict[str, SpecValue]] = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip section headers
            if 'Specifications' in line:
                continue
                
            # Split into parts and clean up
            parts = [p.strip() for p in line.split('-')]
            if len(parts) < 2:
                continue
                
            # First part contains the key and unit
            key_parts = parts[0].split()
            if len(key_parts) < 2:
                continue
                
            # Last part contains the value and qualifier (maximum, minimum, etc)
            value_parts = parts[-1].split()
            if not value_parts:
                continue
                
            # Extract value and unit
            try:
                # Handle temperature ranges like "-40 to +125"
                if 'to' in value_parts:
                    to_idx = value_parts.index('to')
                    # Use the upper bound for ranges
                    value = float(value_parts[to_idx + 1].replace('+', ''))
                else:
                    value = float(value_parts[0])
                
                # Get unit from either key parts or value parts
                unit: Optional[str] = key_parts[-1]
                valid_units = [
                    'vdc', 'amp', 'ohm',
                    'pf', '°c', 'cc', 'mseconds'
                ]
                if unit.lower() in valid_units:
                    # Found unit in key
                    key = ' '.join(key_parts[:-1]).lower()
                else:
                    # Unit might be in value parts
                    has_unit = len(value_parts) > 1
                    unit = value_parts[-1] if has_unit else None
                    key = ' '.join(key_parts).lower()
                
                # Clean up unit
                if unit:
                    replacements = [
                        ('VDC', 'V'), ('Amp', 'A'), ('Ohm', 'Ω'),
                        ('pF', 'pF'), ('°C', '°C'), ('CC', 'cc'),
                        ('mSeconds', 'ms')
                    ]
                    for old, new in replacements:
                        unit = unit.replace(old, new)
                
                # Create SpecValue
                spec_value = SpecValue(value=value, unit=unit)
                
                # Determine category and store value
                if 'power' in key or 'watts' in key:
                    specs.setdefault('power', {})[key] = spec_value
                elif 'voltage' in key or 'breakdown' in key:
                    specs.setdefault('voltage', {})[key] = spec_value
                elif 'current' in key or 'amp' in key:
                    specs.setdefault('current', {})[key] = spec_value
                elif 'resistance' in key:
                    specs.setdefault('resistance', {})[key] = spec_value
                elif 'capacitance' in key:
                    specs.setdefault('capacitance', {})[key] = spec_value
                elif 'temperature' in key or 'storage' in key:
                    specs.setdefault('temperature', {})[key] = spec_value
                elif 'time' in key:
                    specs.setdefault('timing', {})[key] = spec_value
                elif 'volume' in key or 'dimension' in key:
                    specs.setdefault('dimensions', {})[key] = spec_value
                elif 'operate' in key or 'pull' in key:
                    specs.setdefault('operate_point', {})[key] = spec_value
                elif 'release' in key or 'drop' in key:
                    specs.setdefault('release_point', {})[key] = spec_value
            except (ValueError, IndexError):
                continue
        
        return specs

    @classmethod
    def parse_electrical(cls, lines: List[str]) -> ElectricalSpecs:
        """Parse electrical specifications from lines of text."""
        specs = cls._parse_spec_lines(lines)
        return ElectricalSpecs(
            power=specs.get('power', {}),
            voltage=specs.get('voltage', {}),
            current=specs.get('current', {}),
            resistance=specs.get('resistance', {}),
            capacitance=specs.get('capacitance', {})
        )

    @classmethod
    def parse_magnetic(cls, lines: List[str]) -> MagneticSpecs:
        """Parse magnetic specifications from lines of text."""
        specs = cls._parse_spec_lines(lines)
        return MagneticSpecs(
            operate_point=specs.get('operate', {}),
            release_point=specs.get('release', {}),
            pull_in_range=specs.get('pull', {}),
            drop_out_range=specs.get('drop', {})
        )

    @classmethod
    def parse_physical(cls, lines: List[str]) -> PhysicalSpecs:
        """Parse physical specifications from lines of text."""
        specs = cls._parse_spec_lines(lines)
        return PhysicalSpecs(
            dimensions=specs.get('dimensions', {}),
            temperature=specs.get('temperature', {}),
            timing=specs.get('timing', {}),
            material={}  # Material is handled differently as it's str: str
        )

    @classmethod
    def parse_features_advantages(cls, lines: List[str]) -> List[str]:
        """Parse features or advantages into a list of strings."""
        items: List[str] = []
        current_item = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if '•' in line:
                if current_item:
                    items.append(current_item)
                current_item = line.split('•', 1)[1].strip()
            else:
                current_item += " " + line
                
        if current_item:
            items.append(current_item)
            
        return items

    @classmethod
    def parse_notes(cls, lines: List[str]) -> str:
        """Parse notes while maintaining line breaks."""
        return "\n".join(line.strip() for line in lines if line.strip()) 