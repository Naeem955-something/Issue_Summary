import React, { useState } from 'react';
import './ProjectAnalysis.css';

export default function ProjectAnalysis({ token }) {
  const [owner, setOwner] = useState('');
  const [repo, setRepo] = useState('');
  const [loading, setLoading] = useState(false);
  const [projectData, setProjectData] = useState(null);
  const [message, setMessage] = useState('');

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!owner || !repo) return;
    setLoading(true);
    setMessage('');
    setProjectData(null);

    try {
      const res = await fetch(`${API_URL}/api/projects/register?owner=${owner}&repo=${repo}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setMessage(data.message);

      if (data.project_id) {
        // Poll for completion or fetch the profile.
        // For prototype, let's fetch it immediately. If it's building in backend,
        // it might take a couple seconds. Let's wait 1.5 seconds, then fetch it.
        setTimeout(async () => {
          try {
            const projectRes = await fetch(`${API_URL}/api/projects/${data.project_id}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            if (projectRes.ok) {
              const project = await projectRes.json();
              setProjectData(project);
            }
          } catch (err) {
            console.error(err);
          }
        }, 2000);
      }
    } catch (err) {
      console.error(err);
      setMessage('Failed to register project');
    } finally {
      setLoading(false);
    }
  };

  const getScoreClass = (score) => {
    if (score >= 80) return 'high';
    if (score >= 50) return 'medium';
    return 'low';
  };

  const parseLanguages = (langsJson) => {
    try {
      return langsJson ? JSON.parse(langsJson) : {};
    } catch (e) {
      return {};
    }
  };

  const languages = projectData ? parseLanguages(projectData.languages_json) : {};
  const totalLangBytes = Object.values(languages).reduce((sum, val) => sum + val, 0);

  return (
    <div className="project-analysis-card">
      <h3>Repository Analyzer & Maintainer Dashboard</h3>
      <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '16px' }}>
        Register a project to trigger a full technical review, contributor environmental check, and project health report.
      </p>

      <form onSubmit={handleRegister} className="project-form">
        <div className="input-group">
          <label>Repository Owner</label>
          <input
            type="text"
            placeholder="e.g., torvalds"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
          />
        </div>
        <div className="input-group">
          <label>Repository Name</label>
          <input
            type="text"
            placeholder="e.g., linux"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
          />
        </div>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Registering...' : 'Analyze Project'}
        </button>
      </form>

      {message && <p className="status-msg" style={{ fontWeight: '500', color: '#4f46e5', fontSize: '14px' }}>{message}</p>}

      {projectData && (
        <div className="analysis-dashboard">
          <div className="dashboard-header">
            <div className="repo-title">
              <h4>{projectData.repo_owner} / {projectData.repo_name}</h4>
              <div className="repo-meta">
                <span>⭐ {projectData.stars} stars</span>
                <span>🍴 {projectData.forks} forks</span>
                <span>❗ {projectData.open_issues_count} open issues</span>
                {projectData.license && <span>📄 {projectData.license}</span>}
              </div>
            </div>
            <div className="score-badge">
              Platform: <span style={{ color: '#4f46e5' }}>{projectData.platform || 'General'}</span>
            </div>
          </div>

          <div className="metrics-grid">
            <div className="metric-box">
              <h5>Activity Score</h5>
              <div className="score-progress-container">
                <div className="progress-bar-bg">
                  <div 
                    className={`progress-bar-fill ${getScoreClass(projectData.activity_score)}`} 
                    style={{ width: `${projectData.activity_score}%` }}
                  ></div>
                </div>
                <span className="score-text">{projectData.activity_score}/100</span>
              </div>
            </div>

            <div className="metric-box">
              <h5>Beginner Friendliness</h5>
              <div className="score-progress-container">
                <div className="progress-bar-bg">
                  <div 
                    className={`progress-bar-fill ${getScoreClass(projectData.beginner_score)}`} 
                    style={{ width: `${projectData.beginner_score}%` }}
                  ></div>
                </div>
                <span className="score-text">{projectData.beginner_score}/100</span>
              </div>
            </div>

            <div className="metric-box">
              <h5>Contributor Files</h5>
              <div className="checklist-items">
                <div className={`checklist-item ${projectData.has_contributing ? 'verified' : 'missing'}`}>
                  {projectData.has_contributing ? <span className="icon-check">✓</span> : <span className="icon-cross">✗</span>}
                  CONTRIBUTING.md
                </div>
                <div className={`checklist-item ${projectData.has_code_of_conduct ? 'verified' : 'missing'}`}>
                  {projectData.has_code_of_conduct ? <span className="icon-check">✓</span> : <span className="icon-cross">✗</span>}
                  CODE_OF_CONDUCT.md
                </div>
                <div className={`checklist-item ${projectData.has_issue_template ? 'verified' : 'missing'}`}>
                  {projectData.has_issue_template ? <span className="icon-check">✓</span> : <span className="icon-cross">✗</span>}
                  Issue Template
                </div>
                <div className={`checklist-item ${projectData.has_pr_template ? 'verified' : 'missing'}`}>
                  {projectData.has_pr_template ? <span className="icon-check">✓</span> : <span className="icon-cross">✗</span>}
                  PR Template
                </div>
              </div>
            </div>

            <div className="metric-box">
              <h5>Classification</h5>
              <div className="classification-box">
                <div>
                  <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>Primary Domain</span>
                  <span className="class-tag">{projectData.domain_primary || 'Unknown'}</span>
                </div>
                {projectData.domain_secondary && (
                  <div style={{ marginTop: '8px' }}>
                    <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>Secondary Domain</span>
                    <span className="class-tag" style={{ background: '#f1f5f9', color: '#475569' }}>{projectData.domain_secondary}</span>
                  </div>
                )}
                <div style={{ marginTop: '8px' }}>
                  <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>Architecture</span>
                  <span className="class-tag" style={{ background: '#f8fafc', color: '#334155', border: '1px solid #e2e8f0' }}>{projectData.architecture_type || 'Unknown'}</span>
                </div>
              </div>
            </div>
          </div>

          {Object.keys(languages).length > 0 && (
            <div className="languages-section">
              <h5>Languages</h5>
              <div className="lang-bars">
                {Object.entries(languages).map(([lang, bytes], index) => {
                  const percentage = ((bytes / totalLangBytes) * 100).toFixed(1);
                  return (
                    <div key={lang} className="lang-row">
                      <span className="lang-name">{lang}</span>
                      <div className="lang-bar-bg">
                        <div 
                          className="lang-bar-fill" 
                          style={{ 
                            width: `${percentage}%`,
                            background: `hsl(${190 + (index * 40) % 170}, 70%, 50%)`
                          }}
                        ></div>
                      </div>
                      <span className="lang-percent">{percentage}%</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {projectData.health_summary && (
            <div className="health-summary-section">
              <h5>Gemini Health Review Summary</h5>
              <p>{projectData.health_summary}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
