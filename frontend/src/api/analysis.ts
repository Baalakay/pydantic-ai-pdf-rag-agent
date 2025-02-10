export const analyzeQuery = async (modelNumbers: string[]): Promise<AnalysisResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/analysis/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ model_numbers: modelNumbers })
  });

  if (!response.ok) {
    throw new Error('Failed to analyze query');
  }

  return response.json();
}; 