import React, { useState, useRef, useEffect } from 'react';
import './FollowUpChatDrawer.css';

export default function FollowUpChatDrawer({ token, issue, onClose }) {
  const [chatInput, setChatInput] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    // Scroll to bottom on new messages
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [history, loading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || loading) return;

    const userMessage = chatInput.trim();
    setChatInput('');

    // Append developer message to local history
    const updatedHistory = [...history, { role: 'user', content: userMessage }];
    setHistory(updatedHistory);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/issues/${issue.id}/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: userMessage,
          history: updatedHistory
        })
      });

      if (res.ok) {
        const data = await res.json();
        setHistory(prev => [...prev, { role: 'model', content: data.reply }]);
      } else {
        setHistory(prev => [...prev, { role: 'model', content: "Failed to fetch response. Please try again." }]);
      }
    } catch (err) {
      console.error('Chat failed:', err);
      setHistory(prev => [...prev, { role: 'model', content: "Failed to connect to the assistant server." }]);
    } finally {
      setLoading(false);
    }
  };

  if (!issue) return null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-content followup-chat-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <span className="drawer-subtitle">ISSUE COPILOT CHAT</span>
            <h4 className="chat-title-truncate" title={issue.title}>Q&A: {issue.title}</h4>
          </div>
          <button className="close-drawer-btn" onClick={onClose}>✕</button>
        </div>

        <div className="chat-context-banner">
          <span className="info-icon">ℹ</span>
          <p>
            This session is temporary and helps you evaluate task fit. Ask about technical details, codebase structure, or skills.
          </p>
        </div>

        {/* Conversation flow */}
        <div className="chat-messages-container">
          {history.length === 0 ? (
            <div className="empty-chat-state">
              <span className="ai-chat-logo">🤖</span>
              <h5>Ask anything about this issue</h5>
              <p>Gemini is trained on the issue content, project architecture, and your skill profile to give contextual answers.</p>
              <div className="suggested-prompts-grid">
                <button className="suggested-prompt-btn" onClick={() => setChatInput("What parts of the codebase will I need to edit?")}>
                  What codebase parts will I edit?
                </button>
                <button className="suggested-prompt-btn" onClick={() => setChatInput("I am a beginner at this stack. Is this task too hard for me?")}>
                  Is this too hard for my skills?
                </button>
                <button className="suggested-prompt-btn" onClick={() => setChatInput("What is the first step I should take to solve this?")}>
                  What is the first step to take?
                </button>
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {history.map((msg, idx) => (
                <div key={idx} className={`chat-message-row ${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === 'user' ? '👤' : '🤖'}
                  </div>
                  <div className="message-bubble">
                    <p className="msg-txt">{msg.content}</p>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="chat-message-row model loading">
                  <div className="message-avatar">🤖</div>
                  <div className="message-bubble">
                    <span className="loading-dots">
                      <span>.</span><span>.</span><span>.</span>
                    </span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input box */}
        <form onSubmit={handleSend} className="chat-input-bar">
          <input
            type="text"
            placeholder="Have questions about this issue?"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            disabled={loading}
            className="chat-input-field"
            autoFocus
          />
          <button type="submit" className="chat-send-btn" disabled={loading || !chatInput.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
