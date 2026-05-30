import React, { useState } from 'react';
import './IssueCard.css';

export default function IssueCard({ issue, showMatchScore, onHealthClick, onMatchClick, onChatClick }) {
  const [showFullDetails, setShowFullDetails] = useState(false);

  const getDifficultyClass = (diff) => {
    switch (diff?.toLowerCase()) {
      case 'easy': return 'easy';
      case 'medium': return 'medium';
      case 'hard': return 'hard';
      default: return 'medium';
    }
  };

  const getHealthColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'green': return 'green';
      case 'amber': return 'amber';
      case 'red': return 'red';
      default: return 'amber';
    }
  };

  const getMatchColor = (score) => {
    if (score >= 80) return 'green';
    if (score >= 50) return 'amber';
    return 'red';
  };

  return (
    <div className="issue-details-card fade-in">
      <div className="card-top-row">
        <div className="type-badge-container">
          <span className="issue-type-badge">{issue.issue_type || 'Bug Fix'}</span>
          {!issue.coding_required && <span className="non-coding-badge">Non-Coding</span>}
        </div>
        <div className="badge-group">
          {issue.cached && <span className="badge-cached">Cached</span>}
          <span className={`difficulty-badge ${getDifficultyClass(issue.difficulty)}`}>
            {issue.difficulty || 'Medium'}
          </span>
        </div>
      </div>

      <h4 className="issue-title">{issue.title}</h4>

      <p className="summary-desc">{issue.summary}</p>

      {/* Required Skills */}
      {issue.required_skills && issue.required_skills.length > 0 && (
        <div className="skills-row">
          <span className="skills-lbl">Required:</span>
          <div className="skills-list">
            {issue.required_skills.map(s => (
              <span key={s} className="skill-item-badge req">{s}</span>
            ))}
          </div>
        </div>
      )}

      {/* Helpful Skills */}
      {issue.helpful_skills && issue.helpful_skills.length > 0 && (
        <div className="skills-row">
          <span className="skills-lbl">Helpful:</span>
          <div className="skills-list">
            {issue.helpful_skills.map(s => (
              <span key={s} className="skill-item-badge help">{s}</span>
            ))}
          </div>
        </div>
      )}

      {/* Expanded Details Section */}
      {showFullDetails && (
        <div className="expanded-details-body fade-in">
          {issue.estimated_hours && (
            <div className="detail-meta-item">
              <strong>Estimated Effort:</strong> {issue.estimated_hours} hours
            </div>
          )}
          {issue.learning_takeaways && (
            <div className="detail-meta-item">
              <strong>What you'll learn:</strong>
              <p className="takeaway-text">{issue.learning_takeaways}</p>
            </div>
          )}
        </div>
      )}

      <div className="card-actions-row">
        <div className="status-badges-group">
          {/* Health Badge */}
          <button 
            type="button" 
            onClick={onHealthClick}
            className={`metric-button health ${getHealthColor(issue.project_health_status)}`}
            title="Click to view Project Health breakdown report"
          >
            {issue.project_health_score !== undefined ? `${issue.project_health_score}% Health` : 'Health Indicator'}
          </button>

          {/* Match Badge */}
          {showMatchScore && issue.match_score !== undefined && (
            <button 
              type="button" 
              onClick={onMatchClick}
              className={`metric-button match ${getMatchColor(issue.match_score)}`}
              title="Click to view Gemini personal fit explanation"
            >
              {issue.match_score}% Match
            </button>
          )}
        </div>

        <div className="functional-buttons">
          <button 
            className="btn-text" 
            onClick={() => setShowFullDetails(!showFullDetails)}
          >
            {showFullDetails ? 'Hide details' : 'View details'}
          </button>
          
          <button 
            type="button" 
            className="btn-chat-ai" 
            onClick={onChatClick}
            title="Ask Gemini follow-up questions about this issue"
          >
            💬 Ask AI
          </button>
          
          <a 
            href={issue.url} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="btn-apply-github"
          >
            Apply <span>→</span>
          </a>
        </div>
      </div>
    </div>
  );
}
