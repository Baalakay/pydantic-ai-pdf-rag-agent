// Types matching backend output structures
export interface SpecValue {
  unit?: string;
  value: string | number;
}

export interface CategorySpec {
  subcategories: Record<string, SpecValue>;
}

export interface SectionData {
  categories: Record<string, CategorySpec>;
}

export interface PDFData {
  model_name: string;  // Full model name (e.g., "HSR-520R")
  sections: Record<string, SectionData>;
  notes?: Record<string, string>;
  diagram_path?: string;
}

// DataFrame structure from pandas
export interface DataFrame {
  columns: string[];
  data: Record<string, any>[];
}

export interface SpecificationDisplay {
  show: boolean;
  sections: string[];
}

export interface DisplaySections {
  features: boolean;
  advantages: boolean;
  specifications: SpecificationDisplay;
  differences: SpecificationDisplay;
}

export interface FocusSettings {
  section: string;
  category?: string;
  attribute?: string;
}

export interface QueryAnalysis {
  type: 'single' | 'comparison';
  models: string[];
  specific_attribute?: string | null;
  display_sections: DisplaySections;
  focus?: FocusSettings | null;
}

export interface Recommendation {
  action: string;
  model: string;
  context: string;
  category: string;
}

export interface StructuredFindings {
  recommendations: Recommendation[];
  summary: string;
  technical_details: string;
}

export interface AIFindings {
  findings: StructuredFindings;
}

export interface CombinedAnalysis {
  query_analysis: QueryAnalysis;
  findings: AIFindings;
}

export interface ComparisonResult {
  features_df: DataFrame;
  advantages_df: DataFrame;
  specs_df: DataFrame;
  spec_differences_df: DataFrame;
  findings?: AIFindings;
} 