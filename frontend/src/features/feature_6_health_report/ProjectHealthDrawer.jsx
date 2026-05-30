import React, { useState, useEffect } from 'react';
import './ProjectHealthDrawer.css';

export default function ProjectHealthDrawer({ token, projectId, onClose }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_URL}/api/projects/${projectId}/health-report`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setReport(data);
        }
      } catch (err) {
        console.error('Failed to fetch health report:', err);
      } finally {
        setLoading(false);
      }
    };

    if (projectId) {
      fetchReport();
    }
  }, [projectId, token]);

  const getScoreColorClass = (score) => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'amber';
    return 'red';
  };

  if (!projectId) return null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-content project-health-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <span className="drawer-subtitle">PROJECT INSIGHTS</span>
            <h4>Repository Health Assessment</h4>
          </div>
          <button className="close-drawer-btn" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div className="drawer-loading">
            <span className="spinner"></span>
            <p>Analyzing repository telemetry...</p>
          </div>
        ) : report ? (
          <div className="drawer-body">
            <div className="overall-health-card">
              <div className="overall-score-circle-container">
                <div className={`overall-score-circle ${report.overall_rating}`}>
                  <span className="score-number">{report.average_score}</span>
                  <span className="score-label">Health Score</span>
                </div>
              </div>
              <div className="repo-name-header">
                <h5>{report.repo_owner} / {report.repo_name}</h5>
                <span className={`health-rating-badge ${report.overall_rating}`}>
                  {report.overall_rating.toUpperCase()} RATED
                </span>
              </div>
            </div>

            {/* Sub-scores breakdown */}
            <div className="metrics-breakdown-section">
              <h5>Telemetry Sub-scores</h5>
              
              <div className="metric-progress-row">
                <div className="progress-label-row">
                  <span>Activity & Code Velocity</span>
                  <span className="metric-val">{report.sub_scores.activity}%</span>
                </div>
                <div className="progress-bar-bg">
                  <div 
                    className={`progress-bar-fill ${getScoreColorClass(report.sub_scores.activity)}`}
                    style={{ width: `${report.sub_scores.activity}%` }}
                  ></div>
                </div>
                <span className="metric-desc">Derived from commits frequency, stars, forks, and last commit recency.</span>
              </div>

              <div className="metric-progress-row">
                <div className="progress-label-row">
                  <span>Maintainer Responsiveness</span>
                  <span className="metric-val">{report.sub_scores.responsiveness}%</span>
                </div>
                <div className="progress-bar-bg">
                  <div 
                    className={`progress-bar-fill ${getScoreColorClass(report.sub_scores.responsiveness)}`}
                    style={{ width: `${report.sub_scores.responsiveness}%` }}
                  ></div>
                </div>
                <span className="metric-desc">Derived from issue close times and open PR first-response cycles.</span>
              </div>

              <div className="metric-progress-row">
                <div className="progress-label-row">
                  <span>Onboarding Friendliness</span>
                  <span className="metric-val">{report.sub_scores.beginner_friendliness}%</span>
                </div>
                <div className="progress-bar-bg">
                  <div 
                    className={`progress-bar-fill ${getScoreColorClass(report.sub_scores.beginner_friendliness)}`}
                    style={{ width: `${report.sub_scores.beginner_friendliness}%` }}
                  ></div>
                </div>
                <span className="metric-desc">Calculated from the presence of CONTRIBUTING, CoC, and issue/PR templates.</span>
              </div>

              <div className="metric-progress-row">
                <div className="progress-label-row">
                  <span>Documentation Coverage</span>
                  <span className="metric-val">{report.sub_scores.documentation}%</span>
                </div>
                <div className="progress-bar-bg">
                  <div 
                    className={`progress-bar-fill ${getScoreColorClass(report.sub_scores.documentation)}`}
                    style={{ width: `${report.sub_scores.documentation}%` }}
                  ></div>
                </div>
                <span className="metric-desc">Analysis of README completeness, setup guides, and setup automation scripts.</span>
              </div>
            </div>

            {/* Health summary */}
            <div className="report-summary-box">
              <h5>Gemini Strategic Summary</h5>
              <div className="report-quote">
                <p>"{report.health_summary}"</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="drawer-error">
            <p>Failed to retrieve health assessment telemetry.</p>
          </div>
        )}
      </div>
    </div>
  );
}
