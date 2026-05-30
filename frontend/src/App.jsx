import { useState, useEffect } from 'react';
import SkillProfile from './features/feature_1_skill_profile/SkillProfile';
import ProjectAnalysis from './features/feature_2_project_analysis/ProjectAnalysis';
import IssueCard from './features/feature_3_issue_analysis/IssueCard';
import FitExplanationDrawer from './features/feature_5_fit_explanation/FitExplanationDrawer';
import ProjectHealthDrawer from './features/feature_6_health_report/ProjectHealthDrawer';
import AISearchPanel from './features/feature_7_ai_search/AISearchPanel';
import FollowUpChatDrawer from './features/feature_8_followup_chat/FollowUpChatDrawer';
import FeedPersonalizer from './features/feature_9_feed_personalization/FeedPersonalizer';
import './App.css';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')) || null);
  const [owner, setOwner] = useState('');
  const [repo, setRepo] = useState('');
  const [summaries, setSummaries] = useState([]);
  const [originalSummaries, setOriginalSummaries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('issues'); // 'issues', 'profile', 'analyzer'

  // Copilot Feature States
  const [showMatchScore, setShowMatchScore] = useState(false);
  const [selectedHealthProjectId, setSelectedHealthProjectId] = useState(null);
  const [selectedFitIssueId, setSelectedFitIssueId] = useState(null);
  const [selectedChatIssue, setSelectedChatIssue] = useState(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code && !token) {
      setAuthLoading(true);
      fetch(`${API_URL}/api/auth/callback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
        .then((res) => {
          if (!res.ok) throw new Error('Authentication failed');
          return res.json();
        })
        .then((data) => {
          localStorage.setItem('token', data.token);
          localStorage.setItem('user', JSON.stringify(data.user));
          setToken(data.token);
          setUser(data.user);
          window.history.replaceState({}, document.title, '/'); // Remove code from URL
        })
        .catch((err) => {
          setError(err.message);
        })
        .finally(() => {
          setAuthLoading(false);
        });
    }
  }, [token, API_URL]);

  const handleLogin = async () => {
    try {
      const res = await fetch(`${API_URL}/api/auth/github`);
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      setError('Could not initiate login. Make sure backend is running.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    setSummaries([]);
    setOriginalSummaries([]);
    setShowMatchScore(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSummaries([]);
    setOriginalSummaries([]);
    setShowMatchScore(false);

    if (!owner || !repo) {
      setError('Please enter both owner and repo name');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/api/summarize?owner=${owner}&repo=${repo}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.status === 401) {
        handleLogout();
        throw new Error('Session expired. Please log in again.');
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Error: ${response.statusText}`);
      }

      if (data.success) {
        setSummaries(data.summaries);
        setOriginalSummaries(data.summaries);
      } else {
        setError(data.message || 'Failed to fetch summaries');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchResults = (issues) => {
    setSummaries(issues);
    setShowMatchScore(true);
  };

  const handleClearSearch = () => {
    setSummaries(originalSummaries);
    setShowMatchScore(false);
  };

  const handlePersonalizeFeed = (rankedIssues) => {
    setSummaries(rankedIssues);
    setShowMatchScore(true);
  };

  if (!token) {
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="logo-icon">🚀</div>
          <h1>GitHub Issue Summariser</h1>
          <p>AI-powered insights for any open-source repository.</p>
          {error && <div className="error">{error}</div>}
          <button className="btn-primary login-btn" onClick={handleLogin} disabled={authLoading}>
            {authLoading ? 'Authenticating...' : 'Login with GitHub'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-brand">
          <span className="logo-icon-small">🚀</span>
          <h2>Issue Summariser</h2>
        </div>
        <div className="nav-tabs">
          <button className={`nav-tab-btn ${activeTab === 'issues' ? 'active' : ''}`} onClick={() => setActiveTab('issues')}>Summarize Issues</button>
          <button className={`nav-tab-btn ${activeTab === 'profile' ? 'active' : ''}`} onClick={() => setActiveTab('profile')}>Developer Profile</button>
          <button className={`nav-tab-btn ${activeTab === 'analyzer' ? 'active' : ''}`} onClick={() => setActiveTab('analyzer')}>Project Analyzer</button>
        </div>
        <div className="user-profile">
          {user && (
            <>
              <img src={user.avatar_url} alt="Avatar" className="avatar" />
              <span className="username">{user.username}</span>
            </>
          )}
          <button className="btn-secondary" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <main className="main-content">
        {activeTab === 'profile' && <SkillProfile token={token} />}

        {activeTab === 'analyzer' && <ProjectAnalysis token={token} />}

        {activeTab === 'issues' && (
          <>
            <div className="search-card">
              <h3>Summarize Repository Issues</h3>
              <form onSubmit={handleSubmit} className="search-form">
                <div className="input-group">
                  <label>Repository Owner</label>
                  <input
                    type="text"
                    placeholder="e.g., facebook"
                    value={owner}
                    onChange={(e) => setOwner(e.target.value)}
                  />
                </div>
                <div className="input-group">
                  <label>Repository Name</label>
                  <input
                    type="text"
                    placeholder="e.g., react"
                    value={repo}
                    onChange={(e) => setRepo(e.target.value)}
                  />
                </div>
                <button type="submit" className="btn-primary submit-btn" disabled={loading}>
                  {loading ? (
                    <span className="spinner"></span>
                  ) : (
                    'Generate Summaries'
                  )}
                </button>
              </form>
              {error && <div className="error">{error}</div>}
            </div>

            {originalSummaries.length > 0 && (
              <div className="feed-layout-grid fade-in">
                {/* Left Side: Feed */}
                <div className="feed-left-col">
                  {/* Feed Personalizer (Feature 9) */}
                  <FeedPersonalizer 
                    token={token} 
                    currentIssues={originalSummaries} 
                    onPersonalize={handlePersonalizeFeed}
                    onReset={handleClearSearch}
                  />

                  <div className="results-header">
                    <h2>Issue Summaries</h2>
                    <span className="badge-count">{summaries.length} issues</span>
                  </div>

                  {summaries.length === 0 ? (
                    <div className="no-results-state">
                      <p>No matching issues found for your search query.</p>
                      <button className="btn-secondary" onClick={handleClearSearch}>Show All Issues</button>
                    </div>
                  ) : (
                    <div className="issues-grid">
                      {summaries.map((issue) => (
                        <IssueCard 
                          key={issue.id} 
                          issue={issue}
                          showMatchScore={showMatchScore}
                          onHealthClick={() => setSelectedHealthProjectId(issue.project_id)}
                          onMatchClick={() => setSelectedFitIssueId(issue.id)}
                          onChatClick={() => setSelectedChatIssue(issue)}
                        />
                      ))}
                    </div>
                  )}
                </div>

                {/* Right Side: Copilot Panel (Feature 7) */}
                <div className="feed-right-col">
                  <AISearchPanel 
                    token={token}
                    repoOwner={owner}
                    repoName={repo}
                    onSearchResults={handleSearchResults}
                    onClearSearch={handleClearSearch}
                  />
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Conditionally rendered side drawers */}
      {selectedHealthProjectId && (
        <ProjectHealthDrawer 
          token={token}
          projectId={selectedHealthProjectId}
          onClose={() => setSelectedHealthProjectId(null)}
        />
      )}

      {selectedFitIssueId && (
        <FitExplanationDrawer 
          token={token}
          issueId={selectedFitIssueId}
          onClose={() => setSelectedFitIssueId(null)}
        />
      )}

      {selectedChatIssue && (
        <FollowUpChatDrawer 
          token={token}
          issue={selectedChatIssue}
          onClose={() => setSelectedChatIssue(null)}
        />
      )}
    </div>
  );
}

export default App;
