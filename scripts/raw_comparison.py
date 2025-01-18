from app.core.pdf_processor import PDFProcessor
from app.models.comparison import (
    compare_models, 
    create_specs_df,
    ModelSpecs
)


def load_model_data(pdf_path: str) -> ModelSpecs:
    """Load model data from a PDF file."""
    processor = PDFProcessor()
    result = processor.process_pdf(pdf_path)
    
    # Extract model name from filename (e.g. HSR-520R-Series-Rev-K.pdf -> 520R)
    import re
    model_match = re.search(r'HSR-([^-]+)', pdf_path)
    model = model_match.group(1) if model_match else ""
    
    # Create ModelSpecs instance
    return ModelSpecs(
        model_name=model,
        features_advantages=result.features_advantages,
        sections=result.sections
    )


def main() -> None:
    """Run the comparison script."""
    try:
        # Load model data
        model1_path = (
            "uploads/pdfs/b7947df6-147b-4bae-92f8-"
            "bfa9bf6c5b09_HSR-520R-Series-Rev-K.pdf"
        )
        model2_path = (
            "uploads/pdfs/e086919b-3103-4ae3-ac49-"
            "5a1706acdea9_HSR-630-Series.pdf"
        )
        
        models_data = [
            load_model_data(model1_path),
            load_model_data(model2_path)
        ]
        
        # Compare models
        result = compare_models(models_data)
        
        # Print Features and Advantages first
        print("\nFeatures and Advantages:")
        for spec_type in ["features", "advantages"]:
            fa_df = create_specs_df(models_data, spec_type)
            if not fa_df.empty:
                print(f"\n{spec_type.title()}:")
                # Drop any rows where all model values are empty
                model_names = [m.model_name for m in models_data]
                fa_df = fa_df.dropna(subset=model_names, how='all')
                print(result.format_dataframe(fa_df))
        
        # Print specifications by category
        section_names = {
            "Electrical_Specifications": "Electrical Specifications",
            "Magnetic_Specifications": "Magnetic Specifications",
            "Physical_Operational_Specifications": (
                "Physical/Operational Specifications"
            )
        }
        
        for section_key, display_name in section_names.items():
            print(f"\n{display_name}:")
            specs_df = create_specs_df(models_data, section_key)
            if not specs_df.empty:
                print(result.format_dataframe(specs_df))
        
        # Print key differences
        print("\nKey Differences:")
        if not result.spec_differences_df.empty:
            print(result.format_dataframe(result.spec_differences_df))
        else:
            print("No significant differences found.")
        
        # Print AI analysis if available
        if result.ai_analysis:
            print("\nAnalysis of Key Differences:")
            for key, value in result.ai_analysis.items():
                print(f"{key}: {value}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())


if __name__ == "__main__":
    main() 