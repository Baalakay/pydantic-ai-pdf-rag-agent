import { useState } from 'react';

interface ModelSelectorProps {
  selectedModels: string[];
  onCompare: (models: string[]) => void;
  disabled?: boolean;
}

// Available HSR models
const AVAILABLE_MODELS = [
  '980', '980F', '980R',
  '190', '190R',
  '520', '520R',
  '1016', '1016R'
];

export function ModelSelector({ 
  selectedModels, 
  onCompare, 
  disabled = false 
}: ModelSelectorProps) {
  const [models, setModels] = useState<string[]>(selectedModels);

  const handleModelToggle = (model: string) => {
    setModels(current => {
      if (current.includes(model)) {
        return current.filter(m => m !== model);
      }
      // Limit to 4 models maximum
      if (current.length >= 4) {
        return current;
      }
      return [...current, model];
    });
  };

  const handleCompare = () => {
    if (models.length >= 2) {
      onCompare(models);
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <div className="mb-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Select models to compare (2-4):</h3>
        <div className="flex flex-wrap gap-2">
          {AVAILABLE_MODELS.map(model => (
            <button
              key={model}
              onClick={() => handleModelToggle(model)}
              disabled={disabled || (!models.includes(model) && models.length >= 4)}
              className={`
                px-3 py-1 rounded-full text-sm font-medium
                ${models.includes(model)
                  ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                  : 'bg-gray-100 text-gray-800 hover:bg-gray-200'}
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                ${(!models.includes(model) && models.length >= 4) ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              HSR-{model}
            </button>
          ))}
        </div>
      </div>
      
      <button
        onClick={handleCompare}
        disabled={disabled || models.length < 2}
        className={`
          w-full px-4 py-2 rounded-md text-white font-medium
          ${models.length >= 2 && !disabled
            ? 'bg-blue-600 hover:bg-blue-700'
            : 'bg-gray-400 cursor-not-allowed'}
        `}
      >
        Compare {models.length} Models
      </button>
    </div>
  );
} 