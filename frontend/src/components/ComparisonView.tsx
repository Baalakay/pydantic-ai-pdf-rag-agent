interface ComparisonViewProps {
  data: {
    specifications: DataFrame;
    differences: DataFrame;
    features: DataFrame;
    advantages: DataFrame;
    findings?: any;
  }
}

export function ComparisonView({ data }: ComparisonViewProps) {
  console.log("ComparisonView received data:", data);
  
  return (
    <div className="space-y-4">
      <FeatureAdvantageTable 
        features={data.features}
        advantages={data.advantages}
      />
      <SpecificationTable 
        data={data.specifications}
        type="specifications"
      />
      <SpecificationTable 
        data={data.differences}
        type="differences"
        highlightDifferences
      />
    </div>
  );
} 