# Frontend Implementation Strategy

## Architectural Principles

### Core Design Principles
1. **Separation of Concerns**
   - Each component has a single, well-defined responsibility
   - Service logic is separated from data models
   - UI components are decoupled from business logic
   - File system operations are encapsulated in appropriate services

2. **Single Responsibility**
   - Models focus purely on data structure and validation
   - Services handle specific business operations
   - Components manage only their direct concerns
   - Avoid mixing different levels of abstraction

3. **Code Reuse and DRY (Don't Repeat Yourself)**
   - Shared logic is centralized
   - Common patterns are abstracted into reusable components
   - Avoid duplicating business logic across services
   - Use composition over inheritance

4. **Pydantic v2 Best Practices**
   - Models represent data structures only
   - Use computed fields for derived data attributes
   - Keep validation logic in models
   - Leverage type safety throughout

5. **Clean Architecture**
   - Dependencies flow inward
   - Core business logic is independent of UI and infrastructure
   - External concerns (file system, network) are properly abstracted
   - Clear boundaries between layers

### Implementation Guidelines
1. **Service Design**
   - Services should have focused responsibilities
   - External operations (file system, network) should be encapsulated
   - Services should accept simple inputs (e.g., model numbers instead of file paths)
   - Error handling should be consistent and meaningful

2. **Model Design**
   - Models should be pure data structures
   - Use computed fields for derived properties
   - Validation logic belongs in models
   - Keep models focused on their domain

3. **Component Design**
   - Components should be self-contained
   - Props should be well-typed
   - State management should be appropriate to scope
   - Reuse common patterns

4. **Error Handling**
   - Errors should be meaningful and actionable
   - Error boundaries should be at appropriate levels
   - Error states should be user-friendly
   - Logging should be comprehensive

5. **Testing Strategy**
   - Unit tests for isolated functionality
   - Integration tests for service interactions
   - Component tests for UI behavior
   - End-to-end tests for critical paths

These principles should guide all development decisions and code reviews.

## Overview
This document outlines the frontend implementation strategy for the HSR Model Comparison Chat Interface. The interface needs to be embedded as a window on the company website while maintaining full functionality and readability.

## Core Requirements
1. Collapsible sections for all output types
2. Clean, professional appearance
3. Efficient space utilization
4. Responsive design
5. Accessibility compliance
6. Type safety throughout

## Component Structure

### Base Components

#### CollapsibleSection
```typescript
interface CollapsibleSectionProps {
  type: SectionType;
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
  badge?: number | string;
  onToggle?: () => void;
}
```

#### Section Types
```typescript
type SectionType = 
  | 'features_advantages'
  | 'electrical_specs'
  | 'magnetic_specs'
  | 'physical_specs'
  | 'operational_specs'
  | 'diagram'
  | 'notes'
  | 'pdf_preview'
  | 'qr_code'
  | 'ai_analysis'
  | 'differences'
  | 'comparison'
  | 'sources';
```

### Main Components

#### ChatInterface
- Primary container for the chat window
- Handles message display and interaction
- Manages section visibility states
- Implements scrolling behavior

#### ChatSections
- Manages all collapsible sections
- Provides expand/collapse all functionality
- Handles section state management
- Implements section rendering logic

### Specialized Components

#### SpecificationDisplay
```typescript
interface SpecificationDisplayProps {
  type: 'electrical' | 'magnetic' | 'physical' | 'operational';
  data: Record<string, SpecValue>;
  mode: 'single' | 'comparison';
}
```

#### PDFPreview
```typescript
interface PDFPreviewProps {
  pdfUrl: string;
  highlights: {
    page: number;
    content: string;
    section: string;
    boundingBox?: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
  }[];
  onClose: () => void;
}
```

#### QRCodeGenerator
```typescript
interface QRCodeGeneratorProps {
  url: string;
  size?: number;
  includeMargin?: boolean;
  downloadFileName?: string;
}
```

## State Management

### Section Visibility
```typescript
interface SectionVisibility {
  [K in SectionType]: boolean;
}
```

### Chat State
```typescript
interface ChatState {
  messages: ChatMessage[];
  openSections: Set<SectionType>;
  selectedPdf: PDFPreview | null;
  isGeneratingResponse: boolean;
}
```

## Styling Guidelines

### Layout
- Maximum height: 70vh
- Collapsible sections with smooth animations
- Sticky section controls
- Consistent padding and spacing

### Colors
- Primary: #1a73e8
- Background: #ffffff
- Border: #e0e0e0
- Text: #1a1a1a
- Hover: #e9ecef

### Typography
- Font Family: System default
- Base Size: 16px
- Section Headers: 0.9375rem
- Badges: 0.75rem

## Interaction Patterns

### Section Toggling
- Click to expand/collapse
- Optional keyboard shortcuts
- Smooth animations
- Visual feedback on hover

### PDF Preview
- Inline preview with highlights
- Page navigation
- Zoom controls
- Quick source reference

### QR Code
- Generate on demand
- Download options (PNG/SVG)
- Size customization
- Error correction

## Accessibility

### Requirements
- ARIA labels
- Keyboard navigation
- Focus management
- Screen reader support
- Color contrast compliance

## Performance Considerations

### Optimizations
- Lazy loading for PDF preview
- Deferred rendering for hidden sections
- Memoization of expensive calculations
- Efficient re-rendering strategies

## Implementation Phases

### Phase 1: Core Structure
- Base component implementation
- Section management
- Basic styling

### Phase 2: Enhanced Features
- PDF preview
- QR code generation
- Source highlighting

### Phase 3: Optimization
- Performance improvements
- Accessibility implementation
- Mobile responsiveness

## Testing Strategy

### Unit Tests
- Component rendering
- State management
- User interactions

### Integration Tests
- Section interactions
- PDF handling
- Data flow

### Accessibility Tests
- Screen reader compatibility
- Keyboard navigation
- ARIA compliance

## Maintenance Guidelines

### Code Organization
- Consistent file structure
- Clear component boundaries
- Type safety enforcement

### Documentation
- Component documentation
- Props documentation
- State management documentation

## Future Considerations

### Potential Enhancements
- Section reordering
- User preferences
- Enhanced PDF features
- Analytics integration

## Code Implementation

### Type Definitions

#### Model Interfaces
```typescript
interface BaseModel {
  id: string;
  name: string;
}

interface SpecValue {
  value: string;
  unit?: string;
  description?: string;
}

interface CategorySpec {
  [parameter: string]: SpecValue;
}

interface SectionData {
  [category: string]: CategorySpec;
}

interface FeaturesAdvantages {
  features: string[];
  advantages: string[];
}

interface PDFData extends BaseModel {
  sections: SectionData;
  featuresAdvantages: FeaturesAdvantages;
  notes?: string[];
  diagram?: string;
}

interface SpecDifference {
  category: string;
  subcategory?: string;
  parameter: string;
  unit?: string;
  values: Record<string, string>;
}

interface SpecRow {
  category: string;
  subcategory?: string;
  parameter: string;
  unit?: string;
  values: Record<string, SpecValue>;
}

interface ComparisonResult {
  models: string[];
  specifications: SpecRow[];
  differences: Differences;
  features: ModelFeatureAdvantages;
  advantages: ModelFeatureAdvantages;
  aiAnalysis?: string;
}

interface Difference {
  category: string;
  subcategory?: string;
  parameter: string;
  unit?: string;
  values: Record<string, string>;
}

interface Differences {
  items: Difference[];
  has_differences(): boolean;
}

interface FeatureAdvantage {
  item: string;
  models: string[];
}

interface ModelFeatureAdvantages {
  [model: string]: {
    features: string[];
    advantages: string[];
  };
}

interface ModelSpecs {
  [model: string]: {
    [category: string]: {
      [parameter: string]: SpecValue;
    };
  };
}
```

### Component Props Interfaces

#### Display Components
```typescript
interface ComparisonViewProps {
  models: string[];
  onError?: (error: Error) => void;
}

interface SingleModelViewProps {
  model: string;
  onError?: (error: Error) => void;
}

interface SingleSpecViewProps {
  model: string;
  category: string;
  parameter: string;
  onError?: (error: Error) => void;
}

interface FeatureTableProps {
  data: FeatureAdvantage[];
  title: string;
  models: string[];
}

interface SpecificationTableProps {
  specifications: SpecRow[];
  models: string[];
}

interface DifferenceDisplayProps {
  differences: Difference[];
  models: string[];
}

interface AIFindingsProps {
  analysis: string;
  onCopy?: () => void;
}
```

#### Utility Components
```typescript
interface ModelListProps {
  models: string[];
  onModelClick?: (model: string) => void;
  selectedModels?: string[];
}

interface ShareDialogProps {
  url: string;
  onClose: () => void;
}

interface URLShortenerProps {
  longUrl: string;
  onShorten: (shortUrl: string) => void;
}

interface QRCodeProps extends QRCodeGeneratorProps {
  onDownload?: (format: 'svg' | 'png') => void;
}

interface PDFViewerProps extends PDFPreviewProps {
  onPageChange?: (page: number) => void;
  onZoomChange?: (scale: number) => void;
}
```

### Custom Hooks

#### Query Parameters Hook
```typescript
interface ComparisonQueryParams {
  models: string[];
  view: 'comparison' | 'single' | 'spec';
  sections?: string[];
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  filterCategory?: string;
  highlight?: string;
  expanded?: string[];
}

function useComparisonQueryParams() {
  const [searchParams, setSearchParams] = useSearchParams();
  
  const params: ComparisonQueryParams = {
    models: searchParams.get('models')?.split(',') || [],
    view: (searchParams.get('view') as ComparisonQueryParams['view']) || 'comparison',
    sections: searchParams.get('sections')?.split(','),
    sortBy: searchParams.get('sortBy') || undefined,
    sortOrder: (searchParams.get('sortOrder') as 'asc' | 'desc') || undefined,
    filterCategory: searchParams.get('filterCategory') || undefined,
    highlight: searchParams.get('highlight') || undefined,
    expanded: searchParams.get('expanded')?.split(','),
  };

  const updateParams = (newParams: Partial<ComparisonQueryParams>) => {
    const updated = { ...params, ...newParams };
    setSearchParams(
      Object.entries(updated)
        .filter(([_, value]) => value !== undefined && value !== null)
        .reduce((acc, [key, value]) => {
          acc[key] = Array.isArray(value) ? value.join(',') : value;
          return acc;
        }, {} as Record<string, string>)
    );
  };

  return { params, updateParams };
}
```

#### Section Visibility Hook
```typescript
function useSectionVisibility(defaultOpen: SectionType[] = []) {
  const [openSections, setOpenSections] = useState<Set<SectionType>>(
    new Set(defaultOpen)
  );

  const toggleSection = useCallback((section: SectionType) => {
    setOpenSections(prev => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  }, []);

  const expandAll = useCallback(() => {
    setOpenSections(new Set(Object.values(SectionType)));
  }, []);

  const collapseAll = useCallback(() => {
    setOpenSections(new Set());
  }, []);

  return {
    openSections,
    toggleSection,
    expandAll,
    collapseAll,
  };
}
```

### Component Implementations

#### CollapsibleSection Component
```tsx
const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  type,
  title,
  icon,
  children,
  defaultOpen = false,
  badge,
  onToggle,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  
  const handleToggle = () => {
    setIsOpen(!isOpen);
    onToggle?.();
  };

  return (
    <div className="collapsible-section">
      <button
        className="section-header"
        onClick={handleToggle}
        aria-expanded={isOpen}
      >
        <span className="icon">{icon}</span>
        <span className="title">{title}</span>
        {badge && <span className="badge">{badge}</span>}
        <span className={`chevron ${isOpen ? 'open' : ''}`}>▼</span>
      </button>
      <div
        className={`section-content ${isOpen ? 'open' : ''}`}
        aria-hidden={!isOpen}
      >
        {isOpen && children}
      </div>
    </div>
  );
};
```

#### ChatSections Component
```tsx
const ChatSections: React.FC<{
  data: ComparisonResult;
  openSections: Set<SectionType>;
  onToggleSection: (section: SectionType) => void;
}> = ({ data, openSections, onToggleSection }) => {
  return (
    <div className="chat-sections">
      <div className="sections-controls">
        <button onClick={() => onToggleSection('all')}>
          {openSections.size === 0 ? 'Expand All' : 'Collapse All'}
        </button>
      </div>
      
      <CollapsibleSection
        type="features_advantages"
        title="Features & Advantages"
        icon={<FeaturesIcon />}
        defaultOpen={openSections.has('features_advantages')}
        onToggle={() => onToggleSection('features_advantages')}
        badge={data.features.length + data.advantages.length}
      >
        <FeatureTable data={data.features} title="Features" models={data.models} />
        <FeatureTable data={data.advantages} title="Advantages" models={data.models} />
      </CollapsibleSection>

      <CollapsibleSection
        type="specifications"
        title="Specifications"
        icon={<SpecsIcon />}
        defaultOpen={openSections.has('specifications')}
        onToggle={() => onToggleSection('specifications')}
        badge={data.specifications.length}
      >
        <SpecificationTable
          specifications={data.specifications}
          models={data.models}
        />
      </CollapsibleSection>

      {/* Additional sections for differences, diagrams, etc. */}
    </div>
  );
};
```

#### PDFPreview Component
```tsx
const PDFPreview: React.FC<PDFPreviewProps> = ({
  pdfUrl,
  highlights,
  onClose,
}) => {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  return (
    <div className="pdf-preview">
      <div className="pdf-controls">
        <button
          onClick={() => setPageNumber(prev => Math.max(1, prev - 1))}
          disabled={pageNumber <= 1}
        >
          Previous
        </button>
        <span>
          Page {pageNumber} of {numPages}
        </span>
        <button
          onClick={() => setPageNumber(prev => Math.min(numPages, prev + 1))}
          disabled={pageNumber >= numPages}
        >
          Next
        </button>
        <button onClick={() => setScale(prev => prev + 0.1)}>Zoom In</button>
        <button onClick={() => setScale(prev => Math.max(0.1, prev - 0.1))}>
          Zoom Out
        </button>
        <button onClick={onClose}>Close</button>
      </div>

      <Document file={pdfUrl} onLoadSuccess={onDocumentLoadSuccess}>
        <Page
          pageNumber={pageNumber}
          scale={scale}
          renderAnnotationLayer={true}
          renderTextLayer={true}
        >
          {highlights
            .filter(h => h.page === pageNumber)
            .map((highlight, index) => (
              <div
                key={index}
                className="highlight"
                style={{
                  position: 'absolute',
                  ...highlight.boundingBox,
                  backgroundColor: 'rgba(255, 255, 0, 0.3)',
                }}
                title={highlight.content}
              />
            ))}
        </Page>
      </Document>
    </div>
  );
};
```

### Styles

#### Base Styles
```scss
.collapsible-section {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-bottom: 8px;

  .section-header {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    width: 100%;
    background: none;
    border: none;
    cursor: pointer;

    &:hover {
      background-color: #f5f5f5;
    }

    .icon {
      margin-right: 12px;
    }

    .title {
      flex: 1;
      font-weight: 500;
    }

    .badge {
      margin: 0 12px;
      padding: 2px 8px;
      border-radius: 12px;
      background-color: #e0e0e0;
      font-size: 0.75rem;
    }

    .chevron {
      transition: transform 0.2s;
      
      &.open {
        transform: rotate(180deg);
      }
    }
  }

  .section-content {
    padding: 16px;
    border-top: 1px solid #e0e0e0;
    display: none;

    &.open {
      display: block;
    }
  }
}

.chat-sections {
  max-height: 70vh;
  overflow-y: auto;
  padding: 16px;

  .sections-controls {
    position: sticky;
    top: 0;
    background: white;
    padding: 8px 0;
    border-bottom: 1px solid #e0e0e0;
    margin-bottom: 16px;
  }
}

.pdf-preview {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  padding: 24px;

  .pdf-controls {
    background: white;
    padding: 12px;
    border-radius: 4px;
    margin-bottom: 16px;
    display: flex;
    gap: 12px;
    align-items: center;
  }
}
```

## Data Structures

### Backend Integration Types
```typescript
// Core Data Structures matching backend output
interface PDFData {
  model_name: string;  // Full model name (e.g., "HSR-520R")
  sections: {
    [section: string]: SectionData;
  };
  notes?: {
    [key: string]: string;
  };
  diagram_path?: string;
}

interface SectionData {
  categories: {
    [category: string]: CategorySpec;
  };
}

interface CategorySpec {
  subcategories: {
    [subcategory: string]: SpecValue;
  };
}

interface SpecValue {
  unit?: string;
  value: string | number;
}

// Comparison Result Structure
interface ComparisonResult {
  features_df: DataFrame;    // Features comparison
  advantages_df: DataFrame;  // Advantages comparison
  specs_df: DataFrame;      // All specifications
  spec_differences_df: DataFrame;  // Only differing specs
  findings?: AIFindings;    // Optional AI analysis
}

interface DataFrame {
  columns: string[];        // Model numbers as column names
  data: Record<string, any>[];  // Row data
}

interface AIFindings {
  key_differences: string[];
  technical_implications: string[];
  recommendations: Record<string, string>;
}
```

### Component Data Props
```typescript
// Table Display Components
interface SpecificationTableProps {
  data: DataFrame;
  type: 'specifications' | 'differences';
  highlightDifferences?: boolean;
}

interface FeatureAdvantageTableProps {
  data: DataFrame;
  type: 'features' | 'advantages';
}

// Model Information Display
interface ModelInfoProps {
  modelName: string;       // Full model name (e.g., "HSR-520R")
  specifications: {
    category: string;
    spec: string;
    value: string;
  }[];
  features?: string[];
  advantages?: string[];
  diagramPath?: string;
  notes?: string[];
}

// AI Analysis Display
interface AIAnalysisProps {
  findings: AIFindings;
  modelNumbers: string[];  // List of compared models
}
```

## Component Structure

### Main Container
```typescript
interface ComparisonViewProps {
  comparisonResult: ComparisonResult;
  onModelSelect?: (modelName: string) => void;
  onDiagramView?: (path: string) => void;
}
```

### Specialized Components

#### SpecificationComparison
- Handles both full specifications and differences
- Supports column sorting and filtering
- Implements row grouping by category
- Provides expand/collapse by category
```typescript
interface SpecificationComparisonProps {
  specs: DataFrame;
  differences: DataFrame;
  showOnlyDifferences: boolean;
  groupByCategory: boolean;
}
```

#### FeatureAdvantageComparison
- Displays feature and advantage matrices
- Shows checkmarks for applicable models
- Supports filtering and searching
```typescript
interface FeatureAdvantageComparisonProps {
  features: DataFrame;
  advantages: DataFrame;
  showFeatures: boolean;
  showAdvantages: boolean;
}
```

#### AIAnalysisView
- Displays AI-generated insights
- Shows key differences and implications
- Provides model-specific recommendations
```typescript
interface AIAnalysisViewProps {
  findings: AIFindings;
  onRecommendationSelect?: (modelName: string) => void;
}
```

#### DiagramViewer
- Displays model diagrams
- Supports side-by-side comparison
- Implements zoom and pan controls
```typescript
interface DiagramViewerProps {
  diagramPaths: Record<string, string>;  // Model number to path mapping
  selectedModels: string[];
  onClose: () => void;
}
```

## Layout Structure

### Comparison Layout
```typescript
interface ComparisonLayoutProps {
  activeSection: ComparisonSection;
  onSectionChange: (section: ComparisonSection) => void;
}

type ComparisonSection = 
  | 'overview'
  | 'specifications'
  | 'features'
  | 'advantages'
  | 'differences'
  | 'analysis'
  | 'diagrams';
```

### Section Organization
1. Overview
   - Model names and basic info
   - Quick stats and highlights
   - Navigation to detailed sections

2. Specifications
   - Full specification comparison
   - Category-based grouping
   - Sort and filter controls

3. Features & Advantages
   - Side-by-side comparison
   - Checkmark matrix
   - Search and filter

4. Key Differences
   - Highlighted differences
   - Value comparisons
   - Impact analysis

5. AI Analysis
   - Key findings
   - Technical implications
   - Model recommendations

6. Diagrams
   - Side-by-side view
   - Zoom and pan controls
   - Download options

## State Management

### Comparison State
```typescript
interface ComparisonState {
  activeModels: string[];          // Currently selected models
  activeSections: Set<string>;     // Expanded sections
  filterCriteria: FilterCriteria;  // Active filters
  sortConfig: SortConfig;          // Current sort settings
  viewPreferences: ViewPreferences; // User display preferences
}

interface FilterCriteria {
  searchTerm?: string;
  categories?: string[];
  showOnlyDifferences: boolean;
}

interface SortConfig {
  column?: string;
  direction: 'asc' | 'desc';
}

interface ViewPreferences {
  groupByCategory: boolean;
  showFeatures: boolean;
  showAdvantages: boolean;
  showDiagrams: boolean;
}
```

## Implementation Notes

### Data Processing
1. Model name handling
   - Use full model names (e.g., "HSR-520R")
   - Extract short names for display when needed
   - Maintain consistent ordering

2. Table rendering
   - Handle missing values gracefully
   - Support unit formatting
   - Implement proper cell alignment

3. Difference highlighting
   - Visual indicators for differences
   - Tooltip comparisons
   - Value range indicators

### Performance Optimizations
1. Data memoization
   - Cache processed data structures
   - Memoize expensive calculations
   - Implement virtual scrolling for large datasets

2. Rendering optimization
   - Lazy load sections
   - Defer diagram loading
   - Implement proper React.memo usage

### Error Handling
1. Data validation
   - Validate backend response structure
   - Handle missing or malformed data
   - Provide fallback displays

2. User feedback
   - Loading states
   - Error messages
   - Recovery options 