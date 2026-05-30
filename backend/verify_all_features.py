import os
import sys
import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure stdout handles UTF-8 on Windows command prompts
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


from main import app, get_db
from models import Base, User, DeveloperSkill, ProjectAnalysis, Issue, MatchScore

# 1. Setup Test Database
TEST_DATABASE_URL = "sqlite:///./verify_test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestDevCollabAIFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start patcher for httpx.AsyncClient.get
        from unittest.mock import patch, MagicMock
        cls.httpx_patcher = patch("httpx.AsyncClient.get")
        cls.mock_get = cls.httpx_patcher.start()
        
        # Configure mock responses depending on URL
        async def async_get(url, *args, **kwargs):
            url_str = str(url)
            mock_res = MagicMock()
            mock_res.status_code = 200
            
            if "issues" in url_str:
                mock_res.json.return_value = [
                    {
                        "id": 11111,
                        "title": "Fix react profiling button bug",
                        "html_url": "https://github.com/facebook/react/issues/11111",
                        "body": "A small bug in react profiling panel rendering. Needs Javascript and React skill."
                    },
                    {
                        "id": 22222,
                        "title": "Rewrite react build compiler in Rust",
                        "html_url": "https://github.com/facebook/react/issues/22222",
                        "body": "Rewrite the build chain scripts in Rust for high performance compilation."
                    }
                ]
            elif "languages" in url_str:
                mock_res.json.return_value = {"JavaScript": 95000, "HTML": 5000}
            elif "contents" in url_str:
                mock_res.json.return_value = {"name": "CONTRIBUTING.md"}
            elif "readme" in url_str:
                mock_res.json.return_value = {"content": "dGVzdCByZWFkbWU="}  # "test readme" in base64
            else:
                # Repo metadata details
                mock_res.json.return_value = {
                    "id": 10270,
                    "name": "react",
                    "full_name": "facebook/react",
                    "owner": {"login": "facebook"},
                    "stargazers_count": 200000,
                    "forks_count": 40000,
                    "open_issues_count": 100,
                    "license": {"key": "mit"},
                    "created_at": "2013-05-24T16:15:54Z",
                    "pushed_at": "2026-05-28T16:15:54Z",
                    "language": "JavaScript"
                }
            return mock_res
            
        cls.mock_get.side_effect = async_get

        # Create database and tables
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        
        # Insert seed data
        db = TestingSessionLocal()
        
        # Test User
        cls.user = User(
            id=1,
            github_id="mock",
            username="test_developer",
            avatar_url="https://github.com/ghost.png",
            availability_hours=12,
            preferred_domains="web development,systems",
            learning_goals="React,Rust",
            new_skills_detected=True
        )
        db.add(cls.user)
        
        # Test Project
        cls.project = ProjectAnalysis(
            id=1,
            repo_owner="facebook",
            repo_name="react",
            github_repo_id=10270,
            stars=200000,
            forks=40000,
            open_issues_count=100,
            license="mit",
            last_pushed_at=datetime.utcnow() - timedelta(days=2),
            primary_language="JavaScript",
            languages_json='{"JavaScript": 95.0, "HTML": 5.0}',
            architecture_type="library",
            platform="web",
            has_contributing=True,
            has_code_of_conduct=True,
            has_issue_template=True,
            has_pr_template=True,
            activity_score=85,
            beginner_score=90,
            domain_primary="web development",
            domain_secondary="tooling",
            health_summary="Very healthy react project with active contributors."
        )
        db.add(cls.project)
        
        # Test Issue 1 (React, Web Dev, easy)
        cls.issue1 = Issue(
            id=1,
            project_id=1,
            github_issue_id=11111,
            issue_title="Fix react profiling button bug",
            issue_url="https://github.com/facebook/react/issues/11111",
            issue_type="bug fix",
            plain_summary="A small bug in react profiling panel rendering. Needs Javascript and React skill.",
            required_skills="React,JavaScript",
            helpful_skills="CSS",
            difficulty="beginner",
            estimated_hours=4,
            coding_required=True,
            learning_takeaways="Understanding react profiler internals and debugging UI components."
        )
        db.add(cls.issue1)
        
        # Test Issue 2 (Rust, Systems, hard)
        cls.issue2 = Issue(
            id=2,
            project_id=1,
            github_issue_id=22222,
            issue_title="Rewrite react build compiler in Rust",
            issue_url="https://github.com/facebook/react/issues/22222",
            issue_type="new feature",
            plain_summary="Rewrite the build chain scripts in Rust for high performance compilation.",
            required_skills="Rust,compiler",
            helpful_skills="systems",
            difficulty="advanced",
            estimated_hours=30,
            coding_required=True,
            learning_takeaways="Advanced rust compilation optimization and build scripts."
        )
        db.add(cls.issue2)
        
        db.commit()
        db.close()
        
        # Login to get OAuth mock token
        res = cls.client.post("/api/auth/callback", json={"code": "mock_code"})
        cls.token = res.json()["token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def tearDownClass(cls):
        # Stop patcher
        if hasattr(cls, "httpx_patcher"):
            cls.httpx_patcher.stop()
        # Close all active database connections
        engine.dispose()
        # Remove DB file after test runs
        if os.path.exists("./verify_test.db"):
            try:
                os.remove("./verify_test.db")
            except Exception as e:
                print(f"Warning: Could not remove verify_test.db: {e}")

    def test_feature_1_skill_profile(self):
        print("\n--- Testing Feature 1: Developer Skill Profile ---")
        # 1. Clear banner
        res = self.client.post("/api/user/clear-new-skills-banner", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Banner cleared")
        
        # 2. Add manual skill
        skill_payload = {
            "skill_name": "React",
            "category": "frameworks_and_libraries",
            "proficiency": "advanced"
        }
        res = self.client.post("/api/user/skills", json=skill_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("id", res.json())
        skill_id = res.json()["id"]
        
        # 3. Retrieve skills
        res = self.client.get("/api/user/skills", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data["frameworks_and_libraries"]), 1)
        self.assertEqual(data["frameworks_and_libraries"][0]["skill_name"], "React")
        
        # 4. Remove/delete skill
        res = self.client.delete(f"/api/user/skills/{skill_id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Skill removed")
        
        # 5. Get learning goals
        res = self.client.get("/api/user/learning-goals", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("React", res.json()["learning_goals"])
        
        # 6. Update learning goals
        res = self.client.post("/api/user/learning-goals", json={"learning_goals": ["Rust", "TypeScript"]}, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["learning_goals"], ["Rust", "TypeScript"])

        print("   [OK] Feature 1 is WORKING!")

    def test_feature_2_project_analysis(self):
        print("\n--- Testing Feature 2: Project Analysis (Registration & Sync) ---")
        # Register project
        res = self.client.post("/api/projects/register?owner=facebook&repo=react", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("project_id", res.json())
        
        # Fetch registered project
        project_id = res.json()["project_id"]
        res = self.client.get(f"/api/projects/{project_id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["repo_owner"], "facebook")
        self.assertEqual(res.json()["repo_name"], "react")
        print("   [OK] Feature 2 is WORKING!")

    def test_feature_3_issue_analysis_summarization(self):
        print("\n--- Testing Feature 3: Issue Analysis & Summarization ---")
        # Trigger /api/summarize to see synchronized issues with populated analysis
        res = self.client.post("/api/summarize?owner=facebook&repo=react", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertTrue(len(data["summaries"]) > 0)
        
        # Validate that fields mentioned in specifications exist
        summary_obj = data["summaries"][0]
        self.assertIn("issue_type", summary_obj)
        self.assertIn("required_skills", summary_obj)
        self.assertIn("helpful_skills", summary_obj)
        self.assertIn("difficulty", summary_obj)
        self.assertIn("estimated_hours", summary_obj)
        self.assertIn("coding_required", summary_obj)
        self.assertIn("learning_takeaways", summary_obj)
        print("   [OK] Feature 3 is WORKING!")

    def test_feature_4_match_score(self):
        print("\n--- Testing Feature 4: Match Score Calculation ---")
        # Add developer skills for scoring
        self.client.post("/api/user/skills", json={
            "skill_name": "React", "category": "frameworks_and_libraries", "proficiency": "advanced"
        }, headers=self.headers)
        self.client.post("/api/user/skills", json={
            "skill_name": "JavaScript", "category": "languages_and_ecosystems", "proficiency": "intermediate"
        }, headers=self.headers)
        
        # Check match score for Issue 1 (React, JavaScript, CSS)
        res = self.client.post("/api/summarize?owner=facebook&repo=react", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        summaries = res.json()["summaries"]
        
        issue1_summary = next(s for s in summaries if s["id"] == 1)
        # Should have a high match score because skills match, learning goals (React) align, domain matches, and availability fits
        self.assertTrue(issue1_summary["match_score"] > 50)
        print(f"   Match score calculated: {issue1_summary['match_score']}%")
        print("   [OK] Feature 4 is WORKING!")

    def test_feature_5_fit_explanation(self):
        print("\n--- Testing Feature 5: Fit Explanation ---")
        res = self.client.get("/api/matches/1/explanation", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("explanation", data)
        self.assertIn("skills", data)
        self.assertIn("learning_goals", data)
        self.assertIn("domains", data)
        self.assertIn("availability", data)
        self.assertIn("project_health", data)
        self.assertTrue(len(data["explanation"]) > 0)
        print(f"   Fit Explanation: \"{data['explanation'][:70]}...\"")
        print("   [OK] Feature 5 is WORKING!")

    def test_feature_6_project_health(self):
        print("\n--- Testing Feature 6: Project Health Report ---")
        res = self.client.get("/api/projects/1/health-report", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("overall_rating", data)
        self.assertIn("average_score", data)
        self.assertIn("sub_scores", data)
        self.assertIn("health_summary", data)
        self.assertIn("activity", data["sub_scores"])
        self.assertIn("responsiveness", data["sub_scores"])
        self.assertIn("beginner_friendliness", data["sub_scores"])
        self.assertIn("documentation", data["sub_scores"])
        print(f"   Overall Rating: {data['overall_rating'].upper()}, Avg Score: {data['average_score']}%")
        print("   [OK] Feature 6 is WORKING!")

    def test_feature_7_ai_search(self):
        print("\n--- Testing Feature 7: AI Issue Search Box ---")
        # Test natural language query
        res = self.client.get("/api/search?q=need an easy bug fix with react in 5 hours", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("search_parsed", data)
        self.assertIn("issues", data)
        
        # Test "Match by my skills"
        res2 = self.client.get("/api/search?match_by_my_skills=true", headers=self.headers)
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.json()["success"])
        print("   [OK] Feature 7 is WORKING!")

    def test_feature_8_followup_chat(self):
        print("\n--- Testing Feature 8: Issue Follow-Up Chat ---")
        chat_request = {
            "message": "Do I need to know advanced CSS or just basic flexbox?",
            "history": [
                {"role": "user", "content": "Hi, I want to work on this bug."},
                {"role": "model", "content": "Sure! It's a beginner issue involving react profiling rendering."}
            ]
        }
        res = self.client.post("/api/issues/1/chat", json=chat_request, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("reply", res.json())
        print(f"   AI Chat Reply: \"{res.json()['reply'][:70]}...\"")
        print("   [OK] Feature 8 is WORKING!")

    def test_feature_9_feed_personalization(self):
        print("\n--- Testing Feature 9: Conversational Feed Personalization ---")
        personalize_request = {
            "query": "I am bored of frontend, I want Python backend tasks",
            "issues": [
                {
                    "id": 1,
                    "title": "Fix react profiling button bug",
                    "summary": "Fix react profiler internals UI button rendering.",
                    "difficulty": "beginner",
                    "estimated_hours": 4,
                    "required_skills": ["React", "JavaScript"],
                    "helpful_skills": ["CSS"]
                },
                {
                    "id": 2,
                    "title": "Rewrite react build compiler in Python",
                    "summary": "Rewrite compile scripting chain in Python compiler language.",
                    "difficulty": "advanced",
                    "estimated_hours": 30,
                    "required_skills": ["Python", "compiler"],
                    "helpful_skills": ["systems"]
                }
            ]
        }
        res = self.client.post("/api/feed/personalize", json=personalize_request, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("ranked_issues", data)
        self.assertIn("suggested_goals", data)
        
        # Verify Python issue is ranked first due to query "Python backend tasks"
        self.assertEqual(data["ranked_issues"][0]["id"], 2)
        self.assertTrue(data["ranked_issues"][0]["personalization_reason"].startswith("Matches query"))
        self.assertIn("Python", data["suggested_goals"])
        print("   [OK] Feature 9 is WORKING!")

def print_banner():
    banner = """
============================================================
=== DEVCOLLAB AI - 9 FEATURES VERIFICATION TEST SUITE ===
============================================================
Running integration tests for all 9 AI features specified in
DevCollab_AI_Content.txt against a temporary SQLite database.
============================================================
"""
    print(banner)

if __name__ == "__main__":
    print_banner()
    unittest.main()
