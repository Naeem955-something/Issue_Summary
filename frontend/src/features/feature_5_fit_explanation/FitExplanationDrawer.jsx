import React, { useState, useEffect } from 'react';
import './FitExplanationDrawer.css';

export default function FitExplanationDrawer({ token, issueId, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchExplanation = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_URL}/api/matches/${issueId}/explanation`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const resData = await res.json();
          setData(resData);
        }
      } catch (err) {
        console.error('Failed to fetch fit explanation:', err);
      } finally {
        setLoading(false);
      }
    };

    if (issueId) {
      fetchExplanation();
    }
  }, [issueId, token]);

  const getScoreColorClass = (score) => {
    if (score >= 80) return 'green';
    if (score >= 50) return 'amber';
    return 'red';
  };

  if (!issueId) return null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-content fit-explanation-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <span className="drawer-subtitle">MATCH SCORE ANALYSIS</span>
            <h4>Personal Fit Breakdown</h4>
          </div>
          <button className="close-drawer-btn" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div className="drawer-loading">
            <span className="spinner"></span>
            <p>Evaluating developer skill alignment...</p>
          </div>
        ) : data ? (
          <div className="drawer-body">
            {/* Score Banner */}
            <div className="match-score-summary-card">
              <div className={`score-badge-large ${getScoreColorClass(data.score)}`}>
                <span className="score-percent">{data.score}%</span>
                <span className="score-lbl">MATCH</span>
              </div>
              <div className="fit-rating-details">
                <h5>Overall Alignment</h5>
                <p className="alignment-verdict">
                  {data.score >= 80 ? 'Highly Recommended match' : data.score >= 50 ? 'Good matching potential' : 'Some skill gaps detected'}
                </p>
              </div>
            </div>

            {/* AI Fit Explanation */}
            <div className="fit-ai-paragraph-box">
              <h5>Gemini Fit Explanation</h5>
              <div className="ai-explanation-bubble">
                <p>"{data.explanation}"</p>
              </div>
            </div>

            {/* Skill Alignment Table */}
            <div className="skills-table-section">
              <h5>Required & Helpful Skills Match</h5>
              <div className="skills-table-wrapper">
                <table className="skills-align-table">
                  <thead>
                    <tr>
                      <th>Skill</th>
                      <th>Type</th>
                      <th>Your Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {/* Required Skills */}
                    {data.skills.matched_required.map(skill => (
                      <tr key={skill} className="skill-row matched">
                        <td className="skill-nm">{skill}</td>
                        <td><span className="skill-type-badge req">Required</span></td>
                        <td><span className="status-badge match">✓ Matched</span></td>
                      </tr>
                    ))}
                    {data.skills.missing_required.map(skill => (
                      <tr key={skill} className="skill-row missing">
                        <td className="skill-nm">{skill}</td>
                        <td><span className="skill-type-badge req">Required</span></td>
                        <td><span className="status-badge gap-crit">✗ Missing</span></td>
                      </tr>
                    ))}

                    {/* Helpful Skills */}
                    {data.skills.matched_helpful.map(skill => (
                      <tr key={skill} className="skill-row matched">
                        <td className="skill-nm">{skill}</td>
                        <td><span className="skill-type-badge help">Helpful</span></td>
                        <td><span className="status-badge match">✓ Matched</span></td>
                      </tr>
                    ))}
                    {data.skills.missing_helpful.map(skill => (
                      <tr key={skill} className="skill-row missing-help">
                        <td className="skill-nm">{skill}</td>
                        <td><span className="skill-type-badge help">Helpful</span></td>
                        <td><span className="status-badge gap-minor">✗ Missing</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Learning Goals Alignment */}
            <div className="goals-alignment-section">
              <h5>Learning Goals Alignment</h5>
              {data.learning_goals.matched_goals.length > 0 ? (
                <div className="goals-align-positive">
                  <span className="goal-icon">💡</span>
                  <div className="goals-align-text">
                    <span className="goals-title">Direct Goal Alignment!</span>
                    <p>This task overlaps with your learning goals: <strong>{data.learning_goals.matched_goals.join(', ')}</strong>.</p>
                  </div>
                </div>
              ) : (
                <p className="no-goals-message">No overlapping learning goals specified for this issue. Add more goals in your profile!</p>
              )}
            </div>

            {/* Availability vs Effort */}
            <div className="availability-check-section">
              <h5>Availability vs Effort</h5>
              <div className={`availability-card ${data.availability.fits ? 'fits' : 'exceeds'}`}>
                <div className="availability-icon">
                  {data.availability.fits ? '📅' : '⚠️'}
                </div>
                <div className="availability-info">
                  <span className="avail-title">
                    {data.availability.fits ? 'Fits Stated Availability' : 'Exceeds Weekly Availability'}
                  </span>
                  <p>Issue requires roughly <strong>{data.availability.issue_hours} hours</strong>. Stated availability is <strong>{data.availability.user_hours} hours/week</strong>.</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="drawer-error">
            <p>Failed to retrieve match score explanation details.</p>
          </div>
        )}
      </div>
    </div>
  );
}
