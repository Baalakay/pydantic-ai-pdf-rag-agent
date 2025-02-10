# Product Requirements Document: Responsive Model Refactor

## Overview
This document outlines the comprehensive refactoring plan for the product query system, focusing on improved naming conventions, responsive design, and architectural improvements.

## Core Changes

### 1. Agent Role Renaming
```
Previous → New Names
AI Analysis → CX_Agent     // Customer Experience Agent - handles query interpretation & customization
AI Findings → PS_Agent     // Product Specialist Agent - provides technical analysis & recommendations
```

### 2. Core Type Renaming
```
Previous → New Names
SingleQueryResult/ComparisonResult → ProductQueryResponse
Features_And_Advantages → ProductHighlights
Specifications → TechnicalSpecs
Diagram → ProductDrawing
```

## Domain Models

### Product Drawing
```typescript
interface ProductDrawing {
  path: string;
  title: string;          // e.g., "Dimensional Drawing"
  description?: string;   // e.g., "Physical dimensions and mounting specifications"
  dimensions?: {
    width: string;
    height: string;
    depth: string;
  };
}
```

### Core Product Data
```typescript
interface ProductData {
  modelNumber: string;
  drawing?: ProductDrawing;  // Single technical drawing per product
  technicalSpecs: {
    [section: string]: {
      [category: string]: {
        [spec: string]: {
          value: string;
          unit?: string;
        }
      }
    }
  };
  highlights?: ProductHighlights;
  metadata: {
    sourceFile?: string;
    confidence?: number;
  };
}
```

### Agent Response Types
```typescript
interface CXAgentResponse {
  queryType: 'single' | 'multi' | 'specific';
  modelNumbers: string[];
  focusAreas?: {
    section?: string;
    category?: string;
    specification?: string;
  };
  displayPreferences: {
    sectionsToShow: string[];
    highlightedCategories?: string[];
    comparisonMode?: 'full' | 'differences';
    showDifferencesOnly: boolean;
  };
}

interface PSAgentInsights {
  technicalAnalysis: {
    summary: string;
    keyPoints: string[];
    technicalDetails: TechnicalDetail[];
  };
  recommendations: {
    bestUses: string[];
    considerations: string[];
    alternatives?: string[];
  };
  comparativeAnalysis?: {
    advantages: string[];
    tradeoffs: string[];
    keyDifferences: Difference[];
  };
}

interface ProductQueryResponse {
  type: 'single' | 'multi' | 'specific';
  products: Record<string, ProductData>;
  cx_agent: CXAgentResponse;
  ps_agent: PSAgentInsights;
  metadata: QueryMetadata;
}
```

## File Structure

```
src/
├── backend/
│   ├── core/
│   │   ├── agents/
│   │   │   ├── cx_agent.py
│   │   │   └── ps_agent.py
│   │   ├── processors/
│   │   │   ├── product_processor.py   // Previously PDFProcessor
│   │   │   └── query_processor.py     // Previously CompareProcessor
│   │   └── services/
│   │       ├── document_service.py
│   │       └── recommendation_service.py
│   ├── models/
│   │   ├── agents.py
│   │   ├── product.py
│   │   └── query.py
│   └── api/
│       └── routers/
│           ├── product_queries.py
│           └── document_management.py
│
├── frontend/
    └── src/
        ├── components/
        │   ├── agents/
        │   │   ├── CXAgentPanel.tsx
        │   │   └── PSAgentPanel.tsx
        │   ├── product/
        │   │   ├── ProductDrawingPanel.tsx
        │   │   ├── TechnicalSpecsPanel.tsx
        │   │   └── ProductHighlightsPanel.tsx
        │   ├── common/
        │   │   └── responsive/
        │   │       ├── Container.tsx
        │   │       └── Panel.tsx
        │   └── ui/
        │       ├── Accordion.tsx
        │       ├── Button.tsx
        │       └── Input.tsx
        ├── hooks/
        │   ├── useProductQuery.ts
        │   └── useResponsiveLayout.ts
        └── services/
            ├── agents/
            │   ├── cx_agent.ts
            │   └── ps_agent.ts
            └── api.ts
```

## Component Architecture

### Drawing Layouts
```typescript
type DrawingLayout = 'thumbnail' | 'compact' | 'full';

interface ProductDrawingPanelProps {
  drawing: ProductDrawing;
  layout: DrawingLayout;
  onLayoutChange?: (layout: DrawingLayout) => void;
}
```

### Main Product Display
```typescript
const ProductDisplay: React.FC<{
  queryResponse: ProductQueryResponse;
}> = ({ queryResponse }) => {
  const { isMobile } = useResponsiveLayout();
  const [drawingLayout, setDrawingLayout] = useState<DrawingLayout>(
    isMobile ? 'thumbnail' : 'compact'
  );

  return (
    <ResponsiveContainer>
      <CXAgentPanel
        response={cx_agent}
        layout={isMobile ? 'compact' : 'full'}
      />

      {Object.entries(products).map(([modelNumber, product]) => (
        product.drawing && (
          <ProductDrawingPanel
            key={`${modelNumber}-drawing`}
            drawing={product.drawing}
            layout={drawingLayout}
            onLayoutChange={setDrawingLayout}
          />
        )
      ))}

      <TechnicalSpecsPanel
        products={products}
        displayPreferences={cx_agent.displayPreferences}
        layout={isMobile ? 'stacked' : 'sideBySide'}
      />

      <PSAgentPanel
        insights={ps_agent}
        focusArea={cx_agent.focusAreas}
        layout={isMobile ? 'compact' : 'full'}
      />
    </ResponsiveContainer>
  );
};
```

## Backend Integration

```python
class ProductQueryService:
    def __init__(
        self,
        cx_agent: CXAgent,
        ps_agent: PSAgent,
        product_processor: ProductProcessor,
    ):
        self.cx_agent = cx_agent
        self.ps_agent = ps_agent
        self.product_processor = product_processor

    async def process_query(self, query: str) -> ProductQueryResponse:
        # CX Agent interprets query
        cx_response = await self.cx_agent.interpret_query(query)
        
        # Process products based on interpretation
        products = await self.product_processor.process_models(
            cx_response.modelNumbers
        )
        
        # PS Agent analyzes products
        ps_insights = await self.ps_agent.analyze_products(
            products,
            cx_response.focusAreas
        )
        
        return ProductQueryResponse(
            type=cx_response.queryType,
            products=products,
            cx_agent=cx_response,
            ps_agent=ps_insights,
            metadata=self._generate_metadata()
        )
```

## Key Features & Benefits

### 1. Unified Data Model
- Consistent structure for all product data
- Clear separation of concerns between agents
- Flexible display preferences

### 2. Responsive Design
- Mobile-first approach
- Flexible drawing layouts (thumbnail/compact/full)
- Adaptive component rendering

### 3. Enhanced User Experience
- Progressive disclosure of information
- Consistent interaction patterns
- Optimized for different devices

### 4. Maintainable Architecture
- Clear naming conventions
- Modular component structure
- Reusable patterns

## Implementation Phases

### Phase 1: Core Restructuring
- Create new agent models and interfaces
- Set up new directory structure
- Migrate existing code to new locations

### Phase 2: Backend Refactoring
- Implement CX_Agent and PS_Agent
- Update processors to return JSON instead of DataFrames
- Update API endpoints

### Phase 3: Frontend Updates
- Create new component structure
- Implement responsive design
- Update state management

### Phase 4: Mobile Optimization
- Implement mobile-specific layouts
- Add touch interactions
- Optimize performance 