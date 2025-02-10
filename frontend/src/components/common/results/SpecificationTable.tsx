import { type DataFrame } from '@/types/core';
import { useMemo, Fragment } from 'react';
import { DiagramThumbnail } from "./DiagramThumbnail";
import { Accordion } from "../../ui/Accordion";

interface DataRow {
  Category: string;
  Specification: string;
  [key: string]: string | null;  // Model values are strings or null
}

interface SpecificationTableProps {
  data: DataFrame;
  type: 'specifications' | 'differences';
  highlightDifferences?: boolean;
  sections?: string[];
  focus?: {
    section: string;
    category?: string;
    attribute?: string;
  };
  title?: string;
}

export function SpecificationTable({ 
  data, 
  type, 
  highlightDifferences = false,
  sections,
  focus,
  title = "Technical Specifications"
}: SpecificationTableProps) {
  console.log("SpecificationTable received:", {
    data,
    type,
    highlightDifferences,
    sections,
    focus,
    title
  });

  // Add null check for data
  if (!data?.columns) {
    return null;
  }

  const modelColumns = data.columns.filter(col => 
    col !== 'Category' && col !== 'Specification'
  );

  // Group data by section and category
  const groupedData = useMemo(() => {
    // Helper function to determine section based on category
    const determineSection = (category: string): string => {
      const electricalCategories = ['Power', 'Voltage', 'Current', 'Resistance', 'Capacitance'];
      const magneticCategories = ['Pull - In Range', 'Test Coil'];
      
      if (electricalCategories.includes(category)) {
        return 'Electrical Specifications';
      } else if (magneticCategories.includes(category)) {
        return 'Magnetic Specifications';
      }
      return 'Physical/Operational Specifications';
    };

    const groups: Record<string, Record<string, DataRow[]>> = {
      'Electrical Specifications': {},
      'Magnetic Specifications': {},
      'Physical/Operational Specifications': {}
    };
    
    if (!data?.data || !Array.isArray(data.data)) return groups;
    
    (data.data as DataRow[]).forEach((row: DataRow) => {
      const category = row.Category;
      if (!category) return;
      
      const section = determineSection(category);
      
      // Filter by sections if provided
      if (sections && !sections.includes(section)) {
        return;
      }
      
      if (!groups[section][category]) {
        groups[section][category] = [];
      }
      groups[section][category].push(row);
    });
    
    return groups;
  }, [data, sections]);

  return (
    <div className="min-w-[900px] border border-gray-200 rounded-md shadow-sm">
      <Accordion 
        title={<h3 className="font-medium text-white text-left pl-4">{title}</h3>}
        defaultOpen={true}
        className="border-0 shadow-none rounded-none [&>button]:bg-[#f7941c] [&>button]:text-white [&>button]:hover:bg-[#f7941c]/90"
      >
        <div className="border-t border-gray-200">
          {/* Table header */}
          <div className="bg-gray-50 border-b border-gray-200">
            <div style={{
              display: 'grid',
              gridTemplateColumns: `200px minmax(200px, 1fr) repeat(${modelColumns.length}, 180px)`,
              alignItems: 'center',
              width: '100%'
            }}>
              <div className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </div>
              <div className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Specification
              </div>
              {modelColumns.map((col, idx) => (
                <div key={idx} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {col}
                </div>
              ))}
            </div>
          </div>

          {/* Table body */}
          {data.data.map((row: any, idx: number) => (
            <div 
              key={idx}
              className={`${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'} ${
                idx !== data.data.length - 1 ? 'border-b border-gray-200' : ''
              }`}
              style={{
                display: 'grid',
                gridTemplateColumns: `200px minmax(200px, 1fr) repeat(${modelColumns.length}, 180px)`,
                alignItems: 'center',
                width: '100%'
              }}
            >
              <div className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {row.Category}
              </div>
              <div className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {row.Specification}
              </div>
              {modelColumns.map((col) => (
                <div key={col} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {row[col]}
                </div>
              ))}
            </div>
          ))}
        </div>
      </Accordion>
    </div>
  );
} 