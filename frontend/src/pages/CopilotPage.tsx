// src/pages/CopilotPage.tsx
/**
 * BIZIO AI Copilot - Chat Interface
 * Light theme with proper icons
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import copilotApi, {
    type Message,
    type ConversationSummary,
    type ResponseData,
} from '../api/copilot';
import './CopilotPage.css';

// SVG Icons as React components
const SparklesIcon = () => (
    <svg className="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 3l1.912 5.813a2 2 0 001.275 1.275L21 12l-5.813 1.912a2 2 0 00-1.275 1.275L12 21l-1.912-5.813a2 2 0 00-1.275-1.275L3 12l5.813-1.912a2 2 0 001.275-1.275L12 3z" />
    </svg>
);

const HistoryIcon = () => (
    <svg className="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12,6 12,12 16,14" />
    </svg>
);

const PlusIcon = () => (
    <svg className="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="12" y1="5" x2="12" y2="19" />
        <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
);

const SendIcon = () => (
    <svg className="send-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="22" y1="2" x2="11" y2="13" />
        <polygon points="22,2 15,22 11,13 2,9 22,2" />
    </svg>
);

const UserIcon = () => (
    <svg className="avatar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
        <circle cx="12" cy="7" r="4" />
    </svg>
);

const BotIcon = () => (
    <svg className="avatar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="11" width="18" height="10" rx="2" />
        <circle cx="12" cy="5" r="2" />
        <path d="M12 7v4" />
        <line x1="8" y1="16" x2="8" y2="16" />
        <line x1="16" y1="16" x2="16" y2="16" />
    </svg>
);

const WalletIcon = () => (
    <svg className="prompt-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
        <line x1="1" y1="10" x2="23" y2="10" />
    </svg>
);

const PackageIcon = () => (
    <svg className="prompt-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="16.5" y1="9.4" x2="7.5" y2="4.21" />
        <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
        <polyline points="3.27,6.96 12,12.01 20.73,6.96" />
        <line x1="12" y1="22.08" x2="12" y2="12" />
    </svg>
);

const DollarIcon = () => (
    <svg className="prompt-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="12" y1="1" x2="12" y2="23" />
        <path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
    </svg>
);

const SearchIcon = () => (
    <svg className="prompt-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
);

const CheckCircleIcon = () => (
    <svg className="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
        <polyline points="22,4 12,14.01 9,11.01" />
    </svg>
);

const AlertCircleIcon = () => (
    <svg className="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
);

const LinkIcon = () => (
    <svg className="sources-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
        <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
    </svg>
);

const DatabaseIcon = () => (
    <svg className="tool-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
);

const CalculatorIcon = () => (
    <svg className="tool-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="4" y="2" width="16" height="20" rx="2" />
        <line x1="8" y1="6" x2="16" y2="6" />
        <line x1="8" y1="10" x2="8" y2="10" />
        <line x1="12" y1="10" x2="12" y2="10" />
        <line x1="16" y1="10" x2="16" y2="10" />
        <line x1="8" y1="14" x2="8" y2="14" />
        <line x1="12" y1="14" x2="12" y2="14" />
        <line x1="16" y1="14" x2="16" y2="14" />
        <line x1="8" y1="18" x2="8" y2="18" />
        <line x1="12" y1="18" x2="12" y2="18" />
        <line x1="16" y1="18" x2="16" y2="18" />
    </svg>
);

const SettingsIcon = () => (
    <svg className="tool-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
);

const TrashIcon = () => (
    <svg className="delete-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="3,6 5,6 21,6" />
        <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
        <line x1="10" y1="11" x2="10" y2="17" />
        <line x1="14" y1="11" x2="14" y2="17" />
    </svg>
);

// Quick prompts for new conversations
const QUICK_PROMPTS = [
    {
        icon: WalletIcon,
        text: 'Summarize my expenses this month and explain spikes',
    },
    {
        icon: PackageIcon,
        text: 'Find dead stock and propose what to do with it',
    },
    {
        icon: DollarIcon,
        text: 'Suggest retail prices to keep margin ≥ 30%',
    },
    {
        icon: SearchIcon,
        text: 'Find duplicate suppliers or products and propose merges',
    },
];

// Tool icons mapping
const getToolIcon = (toolName: string) => {
    const icons: Record<string, React.FC> = {
        query_db: DatabaseIcon,
        calculate_metrics: CalculatorIcon,
        get_inventory_status: PackageIcon,
        analyze_expenses: WalletIcon,
        find_duplicates: SearchIcon,
        suggest_pricing: DollarIcon,
        create_task: CheckCircleIcon,
        suggest_data_fixes: SettingsIcon,
    };
    return icons[toolName] || SettingsIcon;
};

// Format currency
const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('kk-KZ', {
        style: 'currency',
        currency: 'KZT',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(value);
};

// Message component
interface MessageBubbleProps {
    message: Message;
}

function MessageBubble({ message }: MessageBubbleProps) {
    const { role, content, response_data } = message;

    return (
        <div className={`message ${role}`}>
            <div className="message-avatar">
                {role === 'user' ? <UserIcon /> : <BotIcon />}
            </div>
            <div className="message-content">
                <div className="message-bubble">
                    {content}
                </div>
                {response_data && <ResponseDataCard data={response_data} />}
            </div>
        </div>
    );
}

// Response data card with key numbers, sources, and confidence
interface ResponseDataCardProps {
    data: ResponseData;
}

function ResponseDataCard({ data }: ResponseDataCardProps) {
    const { key_numbers, sources, confidence } = data;

    if (!key_numbers?.length && !sources?.length && !confidence) {
        return null;
    }

    return (
        <div className="response-data">
            {key_numbers && key_numbers.length > 0 && (
                <div className="key-numbers">
                    {key_numbers.map((kn, i) => (
                        <div key={i} className="key-number">
                            <div className="label">{kn.label}</div>
                            <div className="value">
                                {typeof kn.value === 'number' ? formatCurrency(kn.value) : kn.value}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                {confidence && (
                    <div className={`confidence-badge ${confidence.level}`}>
                        {confidence.level === 'high' ? <CheckCircleIcon /> : <AlertCircleIcon />}
                        <span>{confidence.level} confidence</span>
                    </div>
                )}
            </div>

            {sources && sources.length > 0 && (
                <div className="sources">
                    <div className="sources-title">
                        <LinkIcon />
                        Sources
                    </div>
                    <div className="source-links">
                        {sources.slice(0, 10).map((source, i) => (
                            <span key={i} className="source-link">
                                {source}
                            </span>
                        ))}
                        {sources.length > 10 && (
                            <span className="source-link">+{sources.length - 10} more</span>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

// Tool execution indicator
interface ToolExecutionProps {
    name: string;
    status: 'executing' | 'complete';
    preview?: string;
}

function ToolExecution({ name, status, preview }: ToolExecutionProps) {
    const ToolIcon = getToolIcon(name);

    return (
        <div className={`tool-execution ${status}`}>
            <ToolIcon />
            <div>
                <div className="tool-name">{name.replace(/_/g, ' ')}</div>
                <div className="tool-status">
                    {status === 'executing' ? 'Executing...' : preview || 'Complete'}
                </div>
            </div>
        </div>
    );
}

// Typing indicator
function TypingIndicator() {
    return (
        <div className="message assistant">
            <div className="message-avatar">
                <BotIcon />
            </div>
            <div className="message-content">
                <div className="message-bubble">
                    <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Main Copilot Page
export default function CopilotPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [conversationId, setConversationId] = useState<number | null>(null);
    const [conversations, setConversations] = useState<ConversationSummary[]>([]);
    const [showSidebar, setShowSidebar] = useState(false);
    const [streamingContent, setStreamingContent] = useState('');
    const [activeTools, setActiveTools] = useState<ToolExecutionProps[]>([]);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);


    // Load conversations on mount
    useEffect(() => {
        loadConversations();
    }, []);

    // Scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, streamingContent]);

    const loadConversations = async () => {
        try {
            const convs = await copilotApi.listConversations();
            setConversations(convs);
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    };

    const loadConversation = async (id: number) => {
        try {
            const conv = await copilotApi.getConversation(id);
            setConversationId(conv.id);
            setMessages(conv.messages);
            setShowSidebar(false);
        } catch (error) {
            console.error('Failed to load conversation:', error);
        }
    };

    const startNewConversation = () => {
        setConversationId(null);
        setMessages([]);
        setStreamingContent('');
        setActiveTools([]);
        inputRef.current?.focus();
    };

    const deleteConversation = async (id: number, e: React.MouseEvent) => {
        e.stopPropagation(); // Prevent loading the conversation
        if (!window.confirm('Delete this conversation?')) return;

        try {
            await copilotApi.deleteConversation(id);
            setConversations((prev) => prev.filter((c) => c.id !== id));
            // If we deleted the current conversation, clear it
            if (id === conversationId) {
                startNewConversation();
            }
        } catch (error) {
            console.error('Failed to delete conversation:', error);
        }
    };

    const sendMessage = useCallback(async (text: string) => {
        if (!text.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now(),
            role: 'user',
            content: text.trim(),
            created_at: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            // Use non-streaming for reliability
            const response = await copilotApi.chat({
                message: text.trim(),
                conversation_id: conversationId || undefined,
            });

            setConversationId(response.conversation_id);

            const assistantMessage: Message = {
                id: Date.now(),
                role: 'assistant',
                content: response.content,
                response_data: response.response_data,
                tool_calls: response.tool_calls,
                created_at: new Date().toISOString(),
            };

            setMessages((prev) => [...prev, assistantMessage]);
            loadConversations();
        } catch (err) {
            console.error('Chat error:', err);
            // Show error message
            const errorMessage: Message = {
                id: Date.now(),
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    }, [conversationId, isLoading]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input);
        }
    };

    const handleQuickPrompt = (prompt: string) => {
        sendMessage(prompt);
    };

    return (
        <div className="copilot-page">
            {/* Header */}
            <div className="copilot-header">
                <h1>
                    <SparklesIcon />
                    AI Chat
                </h1>
                <div className="header-actions">
                    <button className="header-btn" onClick={() => setShowSidebar(true)}>
                        <HistoryIcon />
                        History
                    </button>
                    <button className="header-btn" onClick={startNewConversation}>
                        <PlusIcon />
                        New Chat
                    </button>
                </div>
            </div>

            {/* Chat Container */}
            <div className="chat-container">
                {/* Messages */}
                <div className="messages-area">
                    {messages.length === 0 && !streamingContent ? (
                        <div className="welcome-message">
                            <h2>How can I help you today?</h2>
                            <p>
                                I can analyze your business data, find insights, detect problems,
                                and suggest improvements. Ask me anything!
                            </p>
                            <div className="quick-prompts">
                                {QUICK_PROMPTS.map((prompt, i) => (
                                    <button
                                        key={i}
                                        className="quick-prompt-btn"
                                        onClick={() => handleQuickPrompt(prompt.text)}
                                    >
                                        <prompt.icon />
                                        <span className="text">{prompt.text}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <>
                            {messages.map((msg) => (
                                <MessageBubble key={msg.id} message={msg} />
                            ))}

                            {/* Active tool executions */}
                            {activeTools.length > 0 && (
                                <div className="message assistant">
                                    <div className="message-avatar">
                                        <BotIcon />
                                    </div>
                                    <div className="message-content">
                                        {activeTools.map((tool, i) => (
                                            <ToolExecution key={i} {...tool} />
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Streaming content */}
                            {streamingContent && (
                                <div className="message assistant">
                                    <div className="message-avatar">
                                        <BotIcon />
                                    </div>
                                    <div className="message-content">
                                        <div className="message-bubble">{streamingContent}</div>
                                    </div>
                                </div>
                            )}

                            {/* Loading indicator */}
                            {isLoading && !streamingContent && activeTools.length === 0 && (
                                <TypingIndicator />
                            )}
                        </>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="input-area">
                    <div className="input-wrapper">
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about your business..."
                            disabled={isLoading}
                        />
                        <button
                            className="send-btn"
                            onClick={() => sendMessage(input)}
                            disabled={!input.trim() || isLoading}
                        >
                            {isLoading ? '...' : <>Send <SendIcon /></>}
                        </button>
                    </div>
                </div>
            </div>

            {/* Conversations Sidebar */}
            <div className={`conversations-sidebar ${showSidebar ? 'open' : ''}`}>
                <div className="sidebar-header">
                    <h3>Conversations</h3>
                    <button className="close-sidebar" onClick={() => setShowSidebar(false)}>
                        ×
                    </button>
                </div>
                <div className="conversation-list">
                    {conversations.map((conv) => (
                        <div
                            key={conv.id}
                            className={`conversation-item ${conv.id === conversationId ? 'active' : ''}`}
                            onClick={() => loadConversation(conv.id)}
                        >
                            <div className="conversation-content">
                                <div className="title">{conv.title || 'New conversation'}</div>
                                <div className="meta">
                                    {new Date(conv.updated_at).toLocaleDateString()} · {conv.message_count} messages
                                </div>
                            </div>
                            <button
                                className="delete-btn"
                                onClick={(e) => deleteConversation(conv.id, e)}
                                title="Delete conversation"
                            >
                                <TrashIcon />
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
