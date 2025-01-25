import type { ComparisonResult } from '@/types/comparison';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  // Upload PDF
  async uploadPdf(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/pdf/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Upload failed');
    }
    return response.json();
  },

  // List PDFs
  async listPdfs() {
    const response = await fetch(`${API_BASE_URL}/pdf/list`);
    if (!response.ok) {
      throw new Error('Failed to fetch PDFs');
    }
    return response.json();
  },

  // Chat with the agent
  async chat(message: string, conversationId?: string) {
    const response = await fetch(`${API_BASE_URL}/chat/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: message,
        conversation_id: conversationId,
      }),
    });
    
    if (!response.ok) {
      throw new Error('Chat request failed');
    }
    return response.json();
  },
};

export async function fetchComparison(modelNumbers: string[]): Promise<ComparisonResult> {
  const response = await fetch(`${API_BASE_URL}/api/compare`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ model_numbers: modelNumbers }),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch comparison data');
  }

  return response.json();
} 