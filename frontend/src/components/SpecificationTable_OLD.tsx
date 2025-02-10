import React, { useMemo } from 'react';

export function SpecificationTable({ data }: { data: any }) {
  // Add data validation
  const processedData = useMemo(() => {
    if (!data?.data) {
      return [];  // Return empty array if data or data.data is undefined
    }

    const result: Record<string, string[]> = {};
    
    try {
      data.data.forEach((item: any) => {
        // Your existing processing logic
      });
    } catch (error) {
      console.error('Error processing data:', error);
      return [];
    }

    return result;
  }, [data]);

  // Add loading and error states
  if (!data) {
    return <div>Loading...</div>;
  }

  if (!data.data) {
    return <div>No data available</div>;
  }

  return (
    // Your existing JSX
  );
} 