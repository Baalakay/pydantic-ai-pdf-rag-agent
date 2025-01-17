from typing import Dict, List, Any, Union
from dataclasses import dataclass, field
import pandas as pd
from openai import OpenAI


@dataclass
class ComparisonResult:
    """Result of comparing multiple models."""
    electrical_specs_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    magnetic_specs_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    physical_specs_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    spec_differences_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    key_findings_df: pd.DataFrame = field(default_factory=pd.DataFrame)


def create_specs_df(
    model_data: List[Union[Dict, List]], 
    spec_type: str
) -> pd.DataFrame:
    """Create specifications dataframe."""
    df_data: List[Dict] = []
    
    # Get section name from spec_type
    section_name = spec_type
    
    for model in model_data:
        # Extract model name and sections
        model_name = ""
        sections = {}
        
        # Handle different input types
        if isinstance(model, dict):
            model_name = model.get("model", "")
            sections = model.get("sections", {})
        elif isinstance(model, list):
            model_name = str(model[0]) if model else ""
            sections = model[1] if len(model) > 1 else {}
        
        if not model_name:
            # Skip if no model name found
            continue
            
        # Ensure sections is a dictionary
        if not isinstance(sections, dict):
            # Skip if sections is not a dictionary
            continue
            
        # Get specs
        specs = sections.get(section_name, {})
        if not isinstance(specs, dict):
            if isinstance(specs, list):
                # Handle list type specs
                row = {
                    "Category": section_name,
                    "Subcategory": "",
                    "Unit": "",
                    model_name: ", ".join(str(x) for x in specs)
                }
                df_data.append(row)
            continue
        
        for category, subcats in specs.items():
            if isinstance(subcats, dict):
                for subcat, details in subcats.items():
                    if isinstance(details, dict):
                        # Handle temperature unit variations
                        unit = details.get("unit", "")
                        if category == "Temperature":
                            unit = "°C"  # Always use simple °C for temperature
                        
                        row = {
                            "Category": category,
                            "Subcategory": subcat if subcat else "",
                            "Unit": unit,
                            model_name: details.get("value", "")
                        }
                    else:
                        row = {
                            "Category": category,
                            "Subcategory": subcat if subcat else "",
                            "Unit": "",
                            model_name: str(details)
                        }
                    
                    # Check if row already exists
                    existing_row = None
                    for r in df_data:
                        category_match = r["Category"] == row["Category"]
                        subcat_match = r["Subcategory"] == row["Subcategory"]
                        if category_match and subcat_match:
                            existing_row = r
                            break
                                
                    if existing_row:
                        existing_row[model_name] = row[model_name]
                    else:
                        df_data.append(row)
            elif isinstance(subcats, list):
                # Handle list type subcategories
                row = {
                    "Category": category,
                    "Subcategory": "",
                    "Unit": "",
                    model_name: ", ".join(map(str, subcats))
                }
                df_data.append(row)
            else:
                # Handle other types by converting to string
                row = {
                    "Category": category,
                    "Subcategory": "",
                    "Unit": "",
                    model_name: str(subcats)
                }
                df_data.append(row)
    
    # Create empty DataFrame with required columns if no data
    if not df_data:
        return pd.DataFrame(
            columns=["Category", "Subcategory", "Unit"]
        )
    
    return pd.DataFrame(df_data)


def create_differences_df(
    electrical_df: pd.DataFrame,
    magnetic_df: pd.DataFrame,
    physical_df: pd.DataFrame
) -> pd.DataFrame:
    """Create specifications differences dataframe."""
    dfs = [electrical_df, magnetic_df, physical_df]
    diff_rows: List[Dict] = []
    
    for df in dfs:
        if df.empty:
            continue
            
        cols = ["Category", "Subcategory", "Unit"]
        model_cols = [col for col in df.columns if col not in cols]
        
        for _, row in df.iterrows():
            # Convert all values to strings for comparison
            values = {
                col: str(row[col]) 
                for col in model_cols 
                if pd.notna(row[col]) and row[col] != ""
            }
            
            if len(set(values.values())) > 1:  # If there are differences
                diff_rows.append({
                    "Category": row["Category"],
                    "Subcategory": row["Subcategory"],
                    "Unit": row["Unit"],
                    **{col: row[col] for col in model_cols}
                })
    
    if not diff_rows:
        cols = ["Category", "Subcategory", "Unit"]
        model_cols = []
        for df in dfs:
            if not df.empty:
                model_cols.extend(
                    col for col in df.columns 
                    if col not in cols and col not in model_cols
                )
        return pd.DataFrame(columns=cols + model_cols)
    
    return pd.DataFrame(diff_rows)


def create_key_findings_df(differences_df: pd.DataFrame) -> pd.DataFrame:
    """Create key findings dataframe using OpenAI to analyze differences."""
    findings: List[Dict] = []
    
    if differences_df.empty:
        return pd.DataFrame(columns=["Finding"])
    
    # Format only the essential comparison data
    comparison_rows = []
    for _, row in differences_df.iterrows():
        category = row["Category"]
        subcategory = row.get("Subcategory", "")
        unit = row.get("Unit", "")
        
        # Get model columns (excluding metadata columns)
        model_cols = [col for col in differences_df.columns 
                     if col not in ["Category", "Subcategory", "Unit"]]
        
        # Format the comparison line
        spec_name = f"{category} {subcategory}".strip()
        values = [f"{col}: {row[col]}" for col in model_cols]
        unit_str = f" ({unit})" if unit else ""
        comparison_rows.append(f"{spec_name}{unit_str} - {' vs '.join(values)}")
    
    differences_text = "\n".join(comparison_rows)
    
    # Create prompt for OpenAI
    prompt_parts = [
        "Analyze these specification differences between two models:",
        differences_text + "\n",
        "Provide key technical insights focusing on:",
        "1. Performance differences",
        "2. Operational capabilities",
        "3. Design implications",
        "4. Advantages/disadvantages\n",
        "Format as numbered findings, one per line."
    ]
    prompt = "\n".join(prompt_parts)

    try:
        client = OpenAI()
        system_msg = (
            "You are an expert technical analyst. Provide concise, "
            "technical analysis of the specification differences."
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse response into findings
        content = response.choices[0].message.content
        if isinstance(content, str):
            # Split by newlines and process each line
            lines = content.split('\n')
            current_finding = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if line starts with a number
                if line[0].isdigit() and '. ' in line[:4]:
                    # If we have a previous finding, add it
                    if current_finding:
                        findings.append({"Finding": current_finding})
                    current_finding = line
                else:
                    # Continuation of previous finding
                    if current_finding:
                        current_finding += " " + line
            
            # Add the last finding
            if current_finding:
                findings.append({"Finding": current_finding})
                
    except Exception as e:
        print(f"Error generating findings: {str(e)}")
        # Fallback to basic findings if OpenAI fails
        cols = ["Category", "Subcategory", "Unit"]
        model_cols = [col for col in differences_df.columns if col not in cols]
        
        for _, row in differences_df.iterrows():
            category = row["Category"]
            subcategory = row["Subcategory"]
            unit = row["Unit"]
            
            values = {
                col: str(row[col])
                for col in model_cols 
                if pd.notna(row[col]) and row[col] != ""
            }
            
            if values:
                finding = f"{category}"
                if subcategory:
                    finding += f" {subcategory}"
                finding += " differs: "
                finding += ", ".join(
                    f"{model}: {value}" 
                    for model, value in values.items()
                )
                if unit:
                    finding += f" ({unit})"
                findings.append({"Finding": finding})
    
    return pd.DataFrame(findings) if findings else pd.DataFrame(
        columns=["Finding"]
    )


def compare_models(model_data: List[Any]) -> ComparisonResult:
    """Compare two models and return a ComparisonResult object."""
    # Validate input type
    if not isinstance(model_data, list):
        raise ValueError("Input must be a list of model dictionaries")

    # Validate model count
    if len(model_data) < 2:
        raise ValueError("At least two models are required for comparison")

    # Transform data to ensure proper dictionary structure
    transformed_data = []
    for model in model_data:
        model_dict = {}
        if isinstance(model, dict):
            model_dict = model.copy()
            # Extract model name from filename if not present
            if "model" not in model_dict:
                filename = model_dict.get("filename", "")
                name = filename.split("_")[0] if filename else ""
                model_dict["model"] = name
        elif isinstance(model, list):
            # Handle list input by converting to dict
            model_dict = {
                "model": str(model[0]) if model else "",
                "sections": model[1] if len(model) > 1 else {},
                "diagram_path": (
                    model[2] if len(model) > 2 else ""
                )
            }
        else:
            continue

        if not model_dict.get("model"):
            continue

        transformed_data.append(model_dict)

    if len(transformed_data) < 2:
        raise ValueError("Need at least 2 valid models to compare")

    # Create comparison result
    result = ComparisonResult()

    try:
        # Create specs dataframes
        result.electrical_specs_df = create_specs_df(
            transformed_data, 
            "Electrical Specifications"
        )
        result.magnetic_specs_df = create_specs_df(
            transformed_data, 
            "Magnetic Specifications"
        )
        result.physical_specs_df = create_specs_df(
            transformed_data, 
            "Physical/Operational Specifications"
        )

        # Create differences dataframe
        result.spec_differences_df = create_differences_df(
            result.electrical_specs_df,
            result.magnetic_specs_df,
            result.physical_specs_df
        )

        # Create key findings dataframe
        result.key_findings_df = create_key_findings_df(
            result.spec_differences_df
        )
    except Exception as e:
        raise

    return result