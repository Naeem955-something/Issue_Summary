import React, { useState } from 'react';
import './FeedPersonalizer.css';

export default function FeedPersonalizer({ token, currentIssues, onPersonalize, onReset, onAddLearningGoal }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [reason, setReason] = useState('');
  const [suggestedGoals, setSuggestedGoals] = useState([]);
  const [successMsg, setSuccessMsg] = useState('');

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handlePersonalize = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setReason('');
    setSuggestedGoals([]);
    setSuccessMsg('');

    // Map currentIssues to the backend model structure
    const formattedIssues = currentIssues.map(issue => ({
      id: issue.id,
      title: issue.title,
      summary: issue.summary || '',
      difficulty: issue.difficulty || 'Medium',
      estimated_hours: issue.estimated_hours || 5,
      required_skills: issue.required_skills || [],
      helpful_skills: issue.helpful_skills || [],
      project_id: issue.project_id,
      url: issue.url,
      issue_type: issue.issue_type,
      coding_required: issue.coding_required,
      learning_takeaways: issue.learning_takeaways,
      match_score: issue.match_score,
      project_health_status: issue.project_health_status,
      project_health_score: issue.project_health_score,
      repo_owner: issue.repo_owner,
      repo_name: issue.repo_name,
      cached: issue.cached
    }));

    try {
      const res = await fetch(`${API_URL}/api/feed/personalize`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: query.trim(),
          issues: formattedIssues
        })
      });

      if (res.ok) {
        const data = await res.json();
        onPersonalize(data.ranked_issues);
        setSuggestedGoals(data.suggested_goals || []);
        
        // Build a friendly explanation message from the first reordered item's personalization reason
        if (data.ranked_issues.length > 0 && data.ranked_issues[0].personalization_reason) {
          setReason(data.ranked_issues[0].personalization_reason);
        } else {
          setReason(`Reordered feed based on: "${query}"`);
        }
      }
    } catch (err) {
      console.error('Personalization failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveGoal = async (goal) => {
    try {
      // 1. Fetch current goals
      const fetchRes = await fetch(`${API_URL}/api/user/learning-goals`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      let currentGoals = [];
      if (fetchRes.ok) {
        const data = await fetchRes.json();
        currentGoals = data.learning_goals || [];
      }

      if (currentGoals.includes(goal)) {
        setSuccessMsg(`"${goal}" is already in your learning goals!`);
        return;
      }

      // 2. Add and update
      const updatedGoals = [...currentGoals, goal];
      const updateRes = await fetch(`${API_URL}/api/user/learning-goals`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ learning_goals: updatedGoals })
      });

      if (updateRes.ok) {
        setSuccessMsg(`Successfully added "${goal}" to learning goals!`);
        setSuggestedGoals(prev => prev.filter(g => g !== goal));
        if (onAddLearningGoal) onAddLearningGoal(goal);
      }
    } catch (err) {
      console.error('Failed to add goal:', err);
    }
  };

  const handleClear = () => {
    setQuery('');
    setReason('');
    setSuggestedGoals([]);
    setSuccessMsg('');
    onReset();
  };

  return (
    <div className="feed-personalizer-container">
      <div 
        className={`personalizer-bar-header ${isExpanded ? 'active' : ''}`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="sparkle-icon">✦</span>
        <span className="header-text">Ask AI to personalize your feed</span>
        <span className="arrow-indicator">{isExpanded ? '▼' : '▶'}</span>
      </div>

      {isExpanded && (
        <div className="personalizer-body fade-in">
          <form onSubmit={handlePersonalize} className="personalize-form">
            <input
              type="text"
              placeholder="e.g., I am learning Rust, show me something I can finish in a weekend"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
              className="personalize-input"
            />
            <div className="personalize-btn-group">
              <button 
                type="submit" 
                className="btn-primary btn-sparkle" 
                disabled={loading || !query.trim()}
              >
                {loading ? 'Personalizing...' : 'Personalize Feed'}
              </button>
              {reason && (
                <button 
                  type="button" 
                  className="btn-secondary" 
                  onClick={handleClear}
                >
                  Reset Feed
                </button>
              )}
            </div>
          </form>

          {reason && (
            <div className="personalizer-result-banner fade-in">
              <span className="sparkle-icon">✦</span>
              <p className="result-reason">{reason}</p>
            </div>
          )}

          {suggestedGoals.length > 0 && (
            <div className="suggested-goals-banner fade-in">
              <span className="sparkle-icon-small">💡</span>
              <span className="suggested-text">AI detected new interest. Want to add to learning goals?</span>
              <div className="suggested-goals-chips">
                {suggestedGoals.map(goal => (
                  <button 
                    key={goal} 
                    className="goal-suggest-chip"
                    onClick={() => handleSaveGoal(goal)}
                  >
                    Add {goal} +
                  </button>
                ))}
              </div>
            </div>
          )}

          {successMsg && (
            <div className="success-toast fade-in">
              <span>{successMsg}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
