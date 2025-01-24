"""Service for comparing PDF specifications."""
from typing import Dict, List, Optional, Any
import pandas as pd
from ..models.comparison import ComparisonResult
from .process_pdf import PDFProcessor
from ..models.pdf import PDFData, SpecValue, SectionData
from ..models.ai_findings import AIFindings
from ..models.features import ModelSpecs


class ComparisonProcessor:
    """Processor for comparing PDFs."""

    def __init__(self) -> None:
        """Initialize the comparison processor."""
        self.pdf_processor = PDFProcessor()

    def _convert_to_model_specs(self, name: str, data: PDFData) -> ModelSpecs:
        """Convert PDFData to ModelSpecs."""
        features_advantages: Dict[str, List[str]] = {}
        if "Features_And_Advantages" in data.sections:
            section = data.sections["Features_And_Advantages"]
            for category in ["Features", "Advantages"]:
                if category in section.categories:
                    spec_value = section.categories[category].subcategories.get("")
                    if (isinstance(spec_value, SpecValue) and
                            isinstance(spec_value.value, str)):
                        features_advantages[category.lower()] = [
                            line.strip() for line in spec_value.value.split("\n")
                            if line.strip()
                        ]

        return ModelSpecs(
            model_name=name,
            features_advantages=features_advantages,
            sections={k: v for k, v in data.sections.items() if k != "Features_And_Advantages"}
        )

    async def compare_models(self, model_numbers: List[str]) -> ComparisonResult:
        """Compare specifications between multiple models."""
        # Collect model data
        models = self._collect_model_data(model_numbers)
        if not models:
            return ComparisonResult(
                features_df=pd.DataFrame(),
                advantages_df=pd.DataFrame(),
                specs_df=pd.DataFrame(),
                spec_differences_df=pd.DataFrame()
            )

        # Get sections in order
        sections = self._get_ordered_sections(models)

        # Process features and advantages
        features_df = self._process_features(models, model_numbers)
        advantages_df = self._process_advantages(models, model_numbers)

        # Process specifications
        specs_df, spec_differences = self._process_specifications(models, model_numbers, sections)

        # Generate AI analysis if there are differences
        ai_findings: Optional[AIFindings] = None
        if spec_differences:
            # Convert differences to format expected by AIFindings.analyze
            analysis_data: Dict[str, Dict[str, str]] = {}
            for diff in spec_differences:
                category_str = str(diff.get("Category", ""))
                spec_str = str(diff.get("Specification", ""))
                if not (category_str and spec_str):
                    continue

                values = {
                    k: str(v) for k, v in diff.items()
                    if k not in ["Category", "Specification"]
                }
                key = f"{category_str} - {spec_str}"
                analysis_data[key] = values

            ai_findings = await AIFindings.analyze(model_numbers, analysis_data)

        return ComparisonResult(
            features_df=features_df,
            advantages_df=advantages_df,
            specs_df=specs_df,
            spec_differences_df=pd.DataFrame(spec_differences) if spec_differences else pd.DataFrame(),
            findings=ai_findings
        )

    def _collect_model_data(self, model_numbers: List[str]) -> Dict[str, PDFData]:
        """Collect PDF data for each model."""
        models: Dict[str, PDFData] = {}
        # Create mapping of input model numbers to full model names
        model_name_map = {}
        for model_num in model_numbers:
            result = self.pdf_processor.process_pdf(model_num)
            full_model = result.model_name.split('-')[1]  # e.g., "980R" from "HSR-980R"
            models[full_model] = result
            model_name_map[model_num] = full_model
        
        # Update the model_numbers list with full model names
        for i, num in enumerate(model_numbers):
            model_numbers[i] = model_name_map[num]
            
        return models

    def _get_ordered_sections(self, models: Dict[str, PDFData]) -> List[str]:
        """Get sections in order from the first model."""
        if not models:
            return []
        # Use first model's section order as reference
        first_model = next(iter(models.values()))
        return list(first_model.sections.keys())

    def _process_specifications(
        self,
        models: Dict[str, PDFData],
        model_numbers: List[str],
        sections: List[str]
    ) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Process specifications from all sections."""
        all_specs: List[Dict[str, Any]] = []
        spec_differences: List[Dict[str, Any]] = []

        for section in sections:
            if section == "Features_And_Advantages":
                continue

            # Get ordered specs from first model that has this section
            ordered_specs = self._get_ordered_specs(models, section)

            # Create rows with values for all models
            for category, specification in ordered_specs:
                row = {
                    "Category": category,
                    "Specification": specification
                }

                # Add values for each model
                values = {}
                for name in model_numbers:
                    if name in models and section in models[name].sections:
                        section_data = models[name].sections[section]
                        value = self._get_spec_value(section_data, category, specification)
                        row[name] = value
                        if value:
                            values[name] = value

                all_specs.append(row)

                # Check for differences
                if len(set(values.values())) > 1:
                    spec_differences.append({
                        "Category": category,
                        "Specification": specification,
                        **values
                    })

        # Add diagram paths as a row
        diagram_row: Dict[str, str] = {
            "Category": "Diagram",
            "Specification": ""
        }
        has_diagrams = False
        for name in model_numbers:
            if name in models:
                model_data = models[name]
                if model_data.diagram_path is not None:
                    diagram_row[name] = model_data.diagram_path
                    has_diagrams = True
                else:
                    diagram_row[name] = ""
            else:
                diagram_row[name] = ""

        if has_diagrams:
            all_specs.append(diagram_row)

        return pd.DataFrame(all_specs), spec_differences

    def _get_ordered_specs(
        self,
        models: Dict[str, PDFData],
        section: str
    ) -> List[tuple[str, str]]:
        """Get specs in order from the first model that has this section."""
        ordered_specs = []

        # Find first model with this section
        for model in models.values():
            if section in model.sections:
                section_data = model.sections[section]
                # Preserve category order
                for category_name, category in section_data.categories.items():
                    # Preserve subcategory order
                    for subcat_name in category.subcategories:
                        # If subcategory name matches category or is empty, use empty string
                        spec_name = "" if not subcat_name or subcat_name == category_name else subcat_name
                        ordered_specs.append((category_name, spec_name))
                break

        return ordered_specs

    def _get_spec_value(
        self,
        section_data: SectionData,
        category: str,
        specification: str
    ) -> str:
        """Get specification value from section data."""
        if category in section_data.categories:
            category_data = section_data.categories[category]
            spec_key = "" if specification == category else specification
            if spec_key in category_data.subcategories:
                spec_value = category_data.subcategories[spec_key]
                # Preserve the exact value, including blank strings
                value = str(spec_value.value)
                unit = spec_value.unit if spec_value.unit else ""
                return f"{value}{f' {unit}' if unit else ''}"
        return ""

    def _process_features(
        self,
        models: Dict[str, PDFData],
        model_numbers: List[str]
    ) -> pd.DataFrame:
        """Process features from all models."""
        return self._process_feature_type(models, model_numbers, "Features")

    def _process_advantages(
        self,
        models: Dict[str, PDFData],
        model_numbers: List[str]
    ) -> pd.DataFrame:
        """Process advantages from all models."""
        return self._process_feature_type(models, model_numbers, "Advantages")

    def _process_feature_type(
        self,
        models: Dict[str, PDFData],
        model_numbers: List[str],
        feature_type: str
    ) -> pd.DataFrame:
        """Process features or advantages from models."""
        rows: List[Dict[str, Any]] = []

        # Process each model in order
        for name in model_numbers:
            if name not in models:
                continue

            model = models[name]
            if "Features_And_Advantages" not in model.sections:
                continue

            section = model.sections["Features_And_Advantages"]
            if feature_type not in section.categories:
                continue

            category = section.categories[feature_type]
            if "" not in category.subcategories:
                continue

            value = category.subcategories[""]
            if not isinstance(value.value, str):
                continue

            # Split into lines and handle wrapped bullet points
            lines = [line.strip() for line in value.value.split('\n') if line.strip()]
            processed_items = []
            current_item = ""

            for line in lines:
                # Check if line starts with bullet point or similar
                if line.startswith('•') or line.startswith('-'):
                    if current_item:  # Save previous item if exists
                        processed_items.append(current_item)
                    current_item = line
                else:
                    # If no bullet point, append to current item with space
                    if current_item:
                        current_item = f"{current_item} {line}"
                    else:  # Handle case where first line might not have bullet
                        current_item = line

            # Add last item if exists
            if current_item:
                processed_items.append(current_item)

            # Create rows from processed items
            for item in processed_items:
                # Check if item already exists
                existing = next((r for r in rows if r["Specification"] == item), None)
                if existing:
                    existing[name] = "✓"
                else:
                    row = {"Specification": item}
                    row.update({n: "✓" if n == name else "" for n in model_numbers})
                    rows.append(row)

        # Create DataFrame and rename Specification column to empty string
        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        if not df.empty:
            df.rename(columns={"Specification": ""}, inplace=True)
        return df