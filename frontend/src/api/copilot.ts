// src/api/copilot.ts
/**
 * API client for the BIZIO AI Copilot
 */
import api from './client';

// Types
export interface ChatRequest {
    message: string;
    conversation_id?: number;
    context_type?: string;
    context_id?: number;
    stream?: boolean;
}

export interface ChatResponse {
    conversation_id: number;
    content: string;
    response_data?: ResponseData;
    tool_calls?: ToolCall[];
    processing_time_ms: number;
}

export interface ResponseData {
    key_numbers?: KeyNumber[];
    sources?: string[];
    confidence?: Confidence;
    has_tool_data?: boolean;
}

export interface KeyNumber {
    label: string;
    value: number | string;
    formula?: string;
    source?: string;
}

export interface Confidence {
    level: 'high' | 'medium' | 'low';
    reason: string;
}

export interface ToolCall {
    name: string;
    arguments: Record<string, any>;
}

export interface ConversationSummary {
    id: number;
    title?: string;
    context_type?: string;
    created_at: string;
    updated_at: string;
    message_count: number;
}

export interface ConversationDetail {
    id: number;
    title?: string;
    context_type?: string;
    context_id?: number;
    created_at: string;
    messages: Message[];
}

export interface Message {
    id: number;
    role: 'user' | 'assistant' | 'system' | 'tool';
    content: string;
    response_data?: ResponseData;
    tool_calls?: ToolCall[];
    created_at: string;
}

export interface DataFixSuggestion {
    id: number;
    fix_type: string;
    entity_type: string;
    changes: Record<string, any>[];
    affected_records: number;
    status: string;
    created_at: string;
}

// Stream event types
export interface StreamEvent {
    type: 'init' | 'tool_call' | 'text' | 'done' | 'error';
    conversation_id?: number;
    name?: string;
    status?: string;
    content?: string;
    result_preview?: string;
    response_data?: ResponseData;
    tool_calls?: ToolCall[];
    processing_time_ms?: number;
    message?: string;
}

// API Methods
export const copilotApi = {
    /**
     * Send a chat message (non-streaming)
     */
    chat: async (request: ChatRequest): Promise<ChatResponse> => {
        const response = await api.post<ChatResponse>('/copilot/chat', request);
        return response.data;
    },

    /**
     * Send a chat message with streaming response
     * Returns an EventSource for SSE
     */
    chatStream: (
        request: ChatRequest,
        onEvent: (event: StreamEvent) => void,
        onError?: (error: Error) => void
    ): (() => void) => {
        const token = localStorage.getItem('auth_token');
        const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';

        // Use fetch with POST for SSE (EventSource only supports GET)
        const controller = new AbortController();

        fetch(`${baseUrl}/copilot/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(request),
            signal: controller.signal,
        })
            .then(async (response) => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const reader = response.body?.getReader();
                const decoder = new TextDecoder();

                if (!reader) {
                    throw new Error('No response body');
                }

                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });

                    // Parse SSE events from buffer
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    let currentEvent = '';
                    let currentData = '';

                    for (const line of lines) {
                        if (line.startsWith('event:')) {
                            currentEvent = line.slice(6).trim();
                        } else if (line.startsWith('data:')) {
                            currentData = line.slice(5).trim();
                        } else if (line === '' && currentData) {
                            try {
                                const parsed = JSON.parse(currentData) as StreamEvent;
                                parsed.type = (currentEvent as StreamEvent['type']) || parsed.type;
                                onEvent(parsed);
                            } catch (e) {
                                console.error('Failed to parse SSE data:', currentData);
                            }
                            currentEvent = '';
                            currentData = '';
                        }
                    }
                }
            })
            .catch((error) => {
                if (error.name !== 'AbortError') {
                    console.error('Stream error:', error);
                    onError?.(error);
                }
            });

        // Return cleanup function
        return () => controller.abort();
    },

    /**
     * List conversations
     */
    listConversations: async (limit: number = 20): Promise<ConversationSummary[]> => {
        const response = await api.get<ConversationSummary[]>('/copilot/conversations', {
            params: { limit },
        });
        return response.data;
    },

    /**
     * Get a conversation with messages
     */
    getConversation: async (conversationId: number): Promise<ConversationDetail> => {
        const response = await api.get<ConversationDetail>(`/copilot/conversations/${conversationId}`);
        return response.data;
    },

    /**
     * Delete a conversation
     */
    deleteConversation: async (conversationId: number): Promise<void> => {
        await api.delete(`/copilot/conversations/${conversationId}`);
    },

    /**
     * List data fix suggestions
     */
    listSuggestions: async (status?: string): Promise<DataFixSuggestion[]> => {
        const response = await api.get<DataFixSuggestion[]>('/copilot/suggestions', {
            params: { status },
        });
        return response.data;
    },

    /**
     * Approve a data fix suggestion
     */
    approveSuggestion: async (suggestionId: number): Promise<{ status: string; message: string }> => {
        const response = await api.post(`/copilot/suggestions/${suggestionId}/approve`);
        return response.data;
    },

    /**
     * Reject a data fix suggestion
     */
    rejectSuggestion: async (suggestionId: number, reason?: string): Promise<{ status: string }> => {
        const response = await api.post(`/copilot/suggestions/${suggestionId}/reject`, null, {
            params: { reason },
        });
        return response.data;
    },
};

export default copilotApi;
