import React, { useState, useEffect } from 'react';
import './SkillProfile.css';

export default function SkillProfile({ token }) {
  const [skills, setSkills] = useState({
    languages_and_ecosystems: [],
    frameworks_and_libraries: [],
    tools_and_infrastructure: [],
    domain_expertise: [],
    new_skills_detected: false
  });
  const [learningGoals, setLearningGoals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isScanning, setIsScanning] = useState(false);

  // States for adding manual skills inline
  const [activeCategoryAdd, setActiveCategoryAdd] = useState(null);
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillProficiency, setNewSkillProficiency] = useState('beginner');

  // States for adding learning goals
  const [newGoal, setNewGoal] = useState('');

  // Banner highlighting state
  const [highlightUnconfirmed, setHighlightUnconfirmed] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const fetchSkills = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/user/skills`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSkills(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLearningGoals = async () => {
    try {
      const res = await fetch(`${API_URL}/api/user/learning-goals`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setLearningGoals(data.learning_goals || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchSkills();
    fetchLearningGoals();
  }, [token]);

  const handleScan = async () => {
    setIsScanning(true);
    try {
      await fetch(`${API_URL}/api/user/sync-skills`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      alert('Skill synchronization started in the background. Refresh in a few moments.');
    } catch (err) {
      console.error(err);
    } finally {
      setIsScanning(false);
    }
  };

  const handleDelete = async (skillId) => {
    try {
      await fetch(`${API_URL}/api/user/skills/${skillId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchSkills();
    } catch (err) {
      console.error(err);
    }
  };

  const handleConfirm = async (skillId) => {
    try {
      await fetch(`${API_URL}/api/user/skills/confirm/${skillId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchSkills();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDismissBanner = async () => {
    try {
      await fetch(`${API_URL}/api/user/clear-new-skills-banner`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setHighlightUnconfirmed(false);
      setSkills(prev => ({ ...prev, new_skills_detected: false }));
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddManualSkill = async (category) => {
    if (!newSkillName.trim()) return;
    try {
      const res = await fetch(`${API_URL}/api/user/skills`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          skill_name: newSkillName.trim(),
          category: category,
          proficiency: newSkillProficiency
        })
      });
      if (res.ok) {
        setNewSkillName('');
        setNewSkillProficiency('beginner');
        setActiveCategoryAdd(null);
        fetchSkills();
      } else {
        const errData = await res.json();
        alert(errData.detail || 'Failed to add skill');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddGoal = async (e) => {
    e.preventDefault();
    if (!newGoal.trim()) return;
    const updatedGoals = [...learningGoals, newGoal.trim()];
    try {
      const res = await fetch(`${API_URL}/api/user/learning-goals`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ learning_goals: updatedGoals })
      });
      if (res.ok) {
        setLearningGoals(updatedGoals);
        setNewGoal('');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteGoal = async (goalToRemove) => {
    const updatedGoals = learningGoals.filter(g => g !== goalToRemove);
    try {
      const res = await fetch(`${API_URL}/api/user/learning-goals`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ learning_goals: updatedGoals })
      });
      if (res.ok) {
        setLearningGoals(updatedGoals);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const renderSkillChips = (categorySkills) => {
    return categorySkills.map((s) => (
      <div 
        key={s.id} 
        className={`skill-chip ${!s.is_confirmed && highlightUnconfirmed ? 'highlight-unconfirmed' : ''}`} 
        title={s.source}
      >
        <span className="skill-name">{s.skill_name}</span>
        <span className={`proficiency-badge ${s.proficiency}`}>
          {s.proficiency}
        </span>
        {!s.is_confirmed && (
          <button 
            className="confirm-btn" 
            onClick={() => handleConfirm(s.id)}
            title="Confirm skill"
          >
            ✓
          </button>
        )}
        <button className="delete-btn" onClick={() => handleDelete(s.id)}>×</button>
      </div>
    ));
  };

  const renderAddInlineForm = (category) => {
    if (activeCategoryAdd !== category) {
      return (
        <button className="add-btn" onClick={() => setActiveCategoryAdd(category)}>+</button>
      );
    }
    return (
      <div className="add-skill-form">
        <input
          type="text"
          className="add-skill-input"
          placeholder="Skill name..."
          value={newSkillName}
          onChange={(e) => setNewSkillName(e.target.value)}
          autoFocus
        />
        <select
          className="add-skill-select"
          value={newSkillProficiency}
          onChange={(e) => setNewSkillProficiency(e.target.value)}
        >
          <option value="beginner">Beg</option>
          <option value="intermediate">Int</option>
          <option value="advanced">Adv</option>
        </select>
        <button className="save-skill-btn" onClick={() => handleAddManualSkill(category)}>✓</button>
        <button className="cancel-skill-btn" onClick={() => setActiveCategoryAdd(null)}>×</button>
      </div>
    );
  };

  return (
    <div className="skill-profile-card">
      <div className="header-row">
        <h3>Developer Skill Profile</h3>
        <button 
          className="btn-secondary" 
          onClick={handleScan}
          disabled={isScanning}
        >
          {isScanning ? 'Scanning...' : 'Re-scan repos'}
        </button>
      </div>

      {skills.new_skills_detected && (
        <div className="new-skills-banner">
          <span>✦ New skills were detected from your recent GitHub activity!</span>
          <div className="banner-actions">
            <button className="btn-banner-action" onClick={() => setHighlightUnconfirmed(true)}>Review</button>
            <button className="btn-banner-dismiss" onClick={handleDismissBanner}>Dismiss</button>
          </div>
        </div>
      )}
      
      {loading ? (
        <p>Loading skills...</p>
      ) : (
        <div className="skills-grid">
          <div className="skill-category">
            <h4>Languages & Ecosystems</h4>
            <div className="chip-container">
              {renderSkillChips(skills.languages_and_ecosystems || [])}
              {renderAddInlineForm("languages_and_ecosystems")}
            </div>
          </div>
          
          <div className="skill-category">
            <h4>Frameworks & Libraries</h4>
            <div className="chip-container">
              {renderSkillChips(skills.frameworks_and_libraries || [])}
              {renderAddInlineForm("frameworks_and_libraries")}
            </div>
          </div>

          <div className="skill-category">
            <h4>Tools & Infrastructure</h4>
            <div className="chip-container">
              {renderSkillChips(skills.tools_and_infrastructure || [])}
              {renderAddInlineForm("tools_and_infrastructure")}
            </div>
          </div>

          <div className="skill-category">
            <h4>Domain Expertise</h4>
            <div className="chip-container">
              {renderSkillChips(skills.domain_expertise || [])}
              {renderAddInlineForm("domain_expertise")}
            </div>
          </div>

          {/* Learning Goals Section */}
          <div className="learning-goals-section">
            <h4>Learning Goals</h4>
            <div className="chip-container">
              {learningGoals.map((goal, idx) => (
                <div key={idx} className="skill-chip learning-goal-chip">
                  <span className="skill-name">{goal}</span>
                  <button className="delete-btn" onClick={() => handleDeleteGoal(goal)}>×</button>
                </div>
              ))}
              <form onSubmit={handleAddGoal} style={{ display: 'inline-flex', gap: '6px', margin: 0 }}>
                <input
                  type="text"
                  placeholder="Add learning goal..."
                  value={newGoal}
                  onChange={(e) => setNewGoal(e.target.value)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '16px',
                    border: '1px solid #cbd5e1',
                    fontSize: '13px',
                    outline: 'none'
                  }}
                />
                <button type="submit" className="add-btn" style={{ width: 'auto', padding: '0 10px' }}>+</button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
