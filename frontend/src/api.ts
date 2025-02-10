import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface ChatQuery {
    question: string;
    max_context_sections?: number;
}

export interface ChatResponse {
    answer: string;
    context_sections: string[];
}

export interface AnalysisQuery {
    text: string;
    max_sections?: number;
}

export interface AnalysisResponse {
    sections: string[];
    summary: string;
}

export const api = {
    async analyzeText(query: AnalysisQuery): Promise<AnalysisResponse> {
        const response = await axios.post(`${API_BASE_URL}/api/analysis/query`, query);
        return response.data;
    },

    async chatQuery(query: ChatQuery): Promise<ChatResponse> {
        const response = await axios.post(`${API_BASE_URL}/chat/query`, query);
        return response.data;
    }
}; 