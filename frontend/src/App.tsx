import { useState } from 'react'
import type { ComparisonResult } from './types/comparison'
import { fetchComparison } from './services/api'
import { SpecificationTable } from './components/comparison/SpecificationTable'
import { FeatureAdvantageTable } from './components/comparison/FeatureAdvantageTable'
import { AIAnalysis } from './components/comparison/AIAnalysis'
import { QueryInput } from './components/comparison/QueryInput'
import { Accordion } from './components/ui/Accordion'
import { ChatbotIcon } from './components/icons/ChatbotIcon'
import type { QueryAnalysis } from './services/ai'
import { ErrorBoundary } from './components/ErrorBoundary'
import { 
  SparklesIcon, 
  CircleStackIcon,
  CpuChipIcon,
  BeakerIcon
} from '@heroicons/react/24/solid'
import './App.css'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AdminPage } from './pages/Admin'

function App() {
  const [comparisonData, setComparisonData] = useState<ComparisonResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentQuery, setCurrentQuery] = useState<QueryAnalysis | null>(null)

  const handleQuery = async (analysis: QueryAnalysis) => {
    setLoading(true)
    setError(null)
    setCurrentQuery(analysis)

    try {
      if (analysis.type === 'comparison') {
        const result = await fetchComparison(analysis.models)
        console.log('Comparison result:', result)
        if (result && analysis.models.length > 1) {
          if (!result.spec_differences_df) {
            result.spec_differences_df = result.specs_df
          }
          console.log('AI Findings:', result.findings)
          setComparisonData(result)
        } else {
          setComparisonData(result)
        }
      } else {
        setError('Single model queries coming soon!')
      }
    } catch (err) {
      console.error('Error in handleQuery:', err)
      setError(err instanceof Error ? err.message : 'Failed to process request')
    } finally {
      setLoading(false)
    }
  }

  console.log('Rendering with findings:', comparisonData?.findings)

  return (
    <Router>
      <Routes>
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/" element={
          <ErrorBoundary>
            <div className="min-h-screen bg-gray-50">
              <div className="container mx-auto pr-4 py-8">
                <div className="flex items-center gap-4 mb-8 pl-4">
                  <div className="relative">
                    <ChatbotIcon className="w-16 h-16 fill-current" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-transparent">
                      Hi, I'm Herm!
                    </h1>
                    <p className="text-lg text-gray-600">
                      The HSI AI Assistant! Ask me anything about our products.
                    </p>
                  </div>
                </div>
                
                {/* Query Input */}
                <div className="mb-8 px-4">
                  <QueryInput
                    onQuery={handleQuery}
                    disabled={loading}
                  />
                </div>

                {loading && (
                  <div className="text-center py-8 px-4">
                    <p>Processing your request...</p>
                  </div>
                )}

                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mx-4">
                    {error}
                  </div>
                )}

                {comparisonData && currentQuery?.type === 'comparison' && currentQuery.display_sections && (
                  <div>
                    <div className="space-y-4">
                      {/* Features and Advantages Section */}
                      {(currentQuery.display_sections.features || currentQuery.display_sections.advantages) && (
                        <div className="px-4">
                          <FeatureAdvantageTable 
                            featuresData={comparisonData.features_df}
                            advantagesData={comparisonData.advantages_df}
                          />
                        </div>
                      )}
                    </div>

                    {/* Specifications Section */}
                    {currentQuery.display_sections.specifications?.show && (
                      <div className="mt-4 px-4">
                        <SpecificationTable
                          data={comparisonData.specs_df}
                          type={currentQuery.type}
                          highlightDifferences={currentQuery.display_sections.specifications?.highlight_differences}
                          sections={currentQuery.display_sections.specifications?.sections}
                          focus={currentQuery.display_sections.specifications?.focus}
                        />
                      </div>
                    )}

                    <div className="space-y-4 mt-4">
                      {/* Differences Section */}
                      {currentQuery.display_sections.specifications?.show && comparisonData.spec_differences_df && (
                        <div className="px-4">
                          <SpecificationTable 
                            data={comparisonData.spec_differences_df}
                            type="differences"
                            sections={currentQuery.display_sections.specifications.sections}
                            focus={currentQuery.focus}
                            highlightDifferences={false}
                            showModelHeaders={false}
                            title="Differences"
                          />
                        </div>
                      )}

                      {/* AI Analysis Section */}
                      {comparisonData?.findings && (
                        <div className="px-4">
                          <div className="min-w-[900px] border border-gray-200 rounded-md shadow-sm">
                            <Accordion title="Herms AI Recommendations" defaultOpen={true} className="p-0 [&>button]:text-left [&>button]:bg-[#f7941c] [&>button]:text-white [&>button]:hover:bg-[#f7941c]/90">
                              <div>
                                <AIAnalysis findings={comparisonData.findings} focus={currentQuery.focus} />
                              </div>
                            </Accordion>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </ErrorBoundary>
        } />
      </Routes>
    </Router>
  )
}

export default App
