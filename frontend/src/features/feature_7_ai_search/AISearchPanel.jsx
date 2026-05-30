import React, { useState } from 'react';
import './AISearchPanel.css';

export default function AISearchPanel({ token, onSearchResults, onClearSearch, repoOwner, repoName }) {
  const [nlpQuery, setNlpQuery] = useState('');
  const [showPreferenceForm, setShowPreferenceForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchTriggered, setSearchTriggered] = useState(false);

  // Preference fields
  const [prefSkills, setPrefSkills] = useState('');
  const [prefDifficulty, setPrefDifficulty] = useState('');
  const [prefMaxHours, setPrefMaxHours] = useState('');
  const [prefIssueType, setPrefIssueType] = useState('');
  const [prefCodingRequired, setPrefCodingRequired] = useState(true);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleNlpSearch = async (e) => {
    e.preventDefault();
    if (!nlpQuery.trim()) return;

    setLoading(true);
    setSearchTriggered(true);

    try {
      const url = new URL(`${API_URL}/api/search`);
      url.searchParams.append('q', nlpQuery.trim());
      if (repoOwner) url.searchParams.append('owner', repoOwner);
      if (repoName) url.searchParams.append('repo', repoName);

      const res = await fetch(url.toString(), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        onSearchResults(data.issues);
      }
    } catch (err) {
      console.error('AI NLP search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMatchByMySkills = async () => {
    setLoading(true);
    setSearchTriggered(true);

    try {
      const url = new URL(`${API_URL}/api/search`);
      url.searchParams.append('match_by_my_skills', 'true');
      if (repoOwner) url.searchParams.append('owner', repoOwner);
      if (repoName) url.searchParams.append('repo', repoName);

      const res = await fetch(url.toString(), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        onSearchResults(data.issues);
      }
    } catch (err) {
      console.error('Match by skills failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePreferenceSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSearchTriggered(true);

    try {
      const url = new URL(`${API_URL}/api/search`);
      if (repoOwner) url.searchParams.append('owner', repoOwner);
      if (repoName) url.searchParams.append('repo', repoName);
      
      if (prefDifficulty) url.searchParams.append('difficulty', prefDifficulty);
      if (prefSkills) url.searchParams.append('skills', prefSkills);
      if (prefMaxHours) url.searchParams.append('max_hours', prefMaxHours);
      if (prefIssueType) url.searchParams.append('issue_type', prefIssueType);
      url.searchParams.append('coding_required', prefCodingRequired ? 'true' : 'false');

      const res = await fetch(url.toString(), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        onSearchResults(data.issues);
      }
    } catch (err) {
      console.error('Preference search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setNlpQuery('');
    setPrefSkills('');
    setPrefDifficulty('');
    setPrefMaxHours('');
    setPrefIssueType('');
    setPrefCodingRequired(true);
    setSearchTriggered(false);
    onClearSearch();
  };

  return (
    <div className="ai-search-card">
      <div className="search-card-header">
        <span className="ai-badge">AI COPILOT</span>
        <h4>Smart Match & AI Search</h4>
      </div>
      <p className="search-description">
        Use natural language or customize preferences to find issues scored to your specific profile.
      </p>

      {/* NLP Search */}
      <form onSubmit={handleNlpSearch} className="nlp-search-form">
        <div className="input-with-button">
          <input
            type="text"
            placeholder="Describe what you want... e.g. Python task under 5 hours"
            value={nlpQuery}
            onChange={(e) => setNlpQuery(e.target.value)}
            disabled={loading}
            className="nlp-input"
          />
          <button type="submit" className="nlp-submit-btn" disabled={loading || !nlpQuery.trim()}>
            🔎
          </button>
        </div>
      </form>

      {/* Skill Match Button */}
      <button 
        type="button" 
        onClick={handleMatchByMySkills} 
        disabled={loading}
        className="btn-primary match-skills-btn"
      >
        ✨ Match by My Skills
      </button>

      {/* Preference Form Toggle */}
      <div className="preference-toggle-row">
        <button 
          className="toggle-pref-form-btn" 
          onClick={() => setShowPreferenceForm(!showPreferenceForm)}
        >
          {showPreferenceForm ? '▼ Hide Detailed Search' : '▶ Search by Preferences'}
        </button>
      </div>

      {showPreferenceForm && (
        <form onSubmit={handlePreferenceSearch} className="preference-search-form fade-in">
          <div className="form-group">
            <label>Specific Skills</label>
            <input
              type="text"
              placeholder="e.g. React, Python, Docker"
              value={prefSkills}
              onChange={(e) => setPrefSkills(e.target.value)}
              className="pref-input"
            />
          </div>

          <div className="form-group">
            <label>Difficulty</label>
            <select
              value={prefDifficulty}
              onChange={(e) => setPrefDifficulty(e.target.value)}
              className="pref-select"
            >
              <option value="">Any Difficulty</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
            </select>
          </div>

          <div className="form-group">
            <label>Max Hours Expected</label>
            <input
              type="number"
              placeholder="e.g. 10"
              value={prefMaxHours}
              onChange={(e) => setPrefMaxHours(e.target.value)}
              className="pref-input"
            />
          </div>

          <div className="form-group">
            <label>Issue Type</label>
            <select
              value={prefIssueType}
              onChange={(e) => setPrefIssueType(e.target.value)}
              className="pref-select"
            >
              <option value="">Any Type</option>
              <option value="Bug Fix">Bug Fix</option>
              <option value="New Feature">New Feature</option>
              <option value="Documentation">Documentation</option>
              <option value="Refactoring">Refactoring</option>
              <option value="Testing">Testing</option>
              <option value="Performance">Performance</option>
            </select>
          </div>

          <div className="form-group-checkbox">
            <input
              type="checkbox"
              id="prefCodingRequired"
              checked={prefCodingRequired}
              onChange={(e) => setPrefCodingRequired(e.target.checked)}
            />
            <label htmlFor="prefCodingRequired">Requires coding changes</label>
          </div>

          <button type="submit" className="btn-secondary pref-submit-btn" disabled={loading}>
            Search Issues
          </button>
        </form>
      )}

      {searchTriggered && (
        <button 
          onClick={handleClear} 
          className="btn-clear-search"
        >
          ✕ Clear Search - Show All
        </button>
      )}
    </div>
  );
}
