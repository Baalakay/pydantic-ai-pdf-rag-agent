# Backend AI Analyzer PRD

## Background
During development, we identified that both the frontend and backend (`backend/src/app/models/ai_findings.py`) were making separate calls to OpenAI for key findings analysis. This redundancy is inefficient and could lead to inconsistencies.

## Approach
We will consolidate all AI analysis functionality in the backend, following best practices for separation of concerns:

1. **Backend Responsibilities**
   - Handle all OpenAI API calls
   - Process and analyze model comparisons
   - Generate structured findings and recommendations
   - Provide clear, RESTful endpoints for the frontend

2. **Frontend Responsibilities**
   - Focus on display and user interaction
   - Make API calls to backend endpoints
   - Handle loading states and error conditions
   - Present AI analysis results in a user-friendly format

## Implementation Details

### Backend Changes
1. **Endpoints**
   - `/api/analysis/query` - Analyze user queries
   - `/api/analysis/combined` - Combined endpoint for query analysis and AI findings

2. **Models**
   - `QueryAnalysis` - Handles query interpretation
   - `AIFindings` - Processes model comparisons and generates recommendations

3. **Response Format**
   ```typescript
   {
     "query_analysis": {
       // Display settings and query interpretation
     },
     "findings": {
       "analysis": string,  // Overall analysis
       "summary": string,   // Key differences summary
       "details": string    // Technical implications
     }
   }
   ```

### Frontend Changes
1. **Remove Direct OpenAI Calls**
   - Remove OpenAI client configuration
   - Update services to use backend endpoints

2. **Component Updates**
   - `QueryInput` - Use backend for query analysis
   - `AIAnalysis` - Display findings from backend
   - Add proper loading states and error handling

## Benefits
1. **Efficiency**
   - Eliminate duplicate API calls
   - Reduce token usage
   - Centralize API key management

2. **Maintainability**
   - Clear separation of concerns
   - Easier to update AI prompts and logic
   - Consistent error handling

3. **User Experience**
   - Faster response times
   - More consistent analysis results
   - Better error feedback

## Status
- Backend endpoints implemented
- Frontend still needs to be updated to use new endpoints
- Testing needed for both components 