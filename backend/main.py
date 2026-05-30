import os
import requests
import httpx
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import google.generativeai as genai
from models import Base, IssueSummary, User
from pathlib import Path
from dotenv import load_dotenv
import sys

# Add features directory to sys.path so modules can import from main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load .env relative to main.py
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# ============= SETUP =============
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"DEBUG: Loaded API Key at startup: {GEMINI_API_KEY[:10]}...{'*' * 5}" if GEMINI_API_KEY else "DEBUG: GEMINI_API_KEY is NOT loaded!")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey_change_me_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# FastAPI app
app = FastAPI(title="GitHub Issue Summariser API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Gemini AI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ============= HELPER FUNCTIONS =============
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_jwt_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def fetch_issues(owner: str, repo: str) -> list:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    try:
        response = requests.get(
            url,
            headers=headers,
            params={"state": "open", "per_page": 10},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"GitHub API error: {str(e)}")

def summarize_with_gemini(title: str, body: str) -> str:
    if not GEMINI_API_KEY:
        return "Gemini API Key is not configured. This is a mock summary."
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"""
        Summarize this GitHub issue in exactly 3 sentences:
        1. What is the problem?
        2. What needs to be done?
        3. What skills are needed?
        
        Title: {title}
        Body: {body}
        
        Provide only the 3 sentences, nothing else.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

# ============= API ENDPOINTS =============

from features.feature_1_skill_profile.router import router as skill_router
from features.feature_2_project_analysis.router import router as project_router
from features.feature_4_match_scoring.router import router as match_router
from features.feature_5_fit_explanation.router import router as fit_router
from features.feature_6_health_report.router import router as health_router
from features.feature_7_ai_search.router import router as search_router
from features.feature_8_followup_chat.router import router as chat_router
from features.feature_9_feed_personalization.router import router as personalize_router

app.include_router(skill_router)
app.include_router(project_router)
app.include_router(match_router)
app.include_router(fit_router)
app.include_router(health_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(personalize_router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "GitHub Issue Summariser API"}


@app.get("/api/auth/github")
async def github_login():
    """Return the GitHub OAuth authorize URL"""
    if not GITHUB_CLIENT_ID:
        # If no Client ID is provided, simulate a redirect back to the frontend with a mock code
        return {"url": "http://localhost:5173/?code=mock_code_for_testing"}
    url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=read:user"
    return {"url": url}

@app.post("/api/auth/callback")
async def github_callback(request: Request, db: Session = Depends(get_db)):
    """Handle OAuth callback, fetch token, fetch user profile, create/return JWT"""
    data = await request.json()
    code = data.get("code")
    
    if not code:
        raise HTTPException(status_code=400, detail="Code is required")
        
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        # Mock auth for dev if no creds
        user = db.query(User).filter(User.github_id == "mock").first()
        if not user:
            user = User(github_id="mock", username="mock_user", avatar_url="https://github.com/ghost.png")
            db.add(user)
            db.commit()
            db.refresh(user)
        token = create_jwt_token(user.id)
        return {"token": token, "user": {"username": user.username, "avatar_url": user.avatar_url}}

    # 1. Exchange code for access_token
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code
            },
            headers={"Accept": "application/json"}
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")
            
        # 2. Fetch user profile
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_data = user_res.json()
        
        github_id = str(user_data.get("id"))
        username = user_data.get("login")
        avatar_url = user_data.get("avatar_url")
        
        # 3. Create or update user in DB
        user = db.query(User).filter(User.github_id == github_id).first()
        if not user:
            user = User(github_id=github_id, username=username, avatar_url=avatar_url)
            db.add(user)
        else:
            user.username = username
            user.avatar_url = avatar_url
            
        db.commit()
        db.refresh(user)
        
        # 4. Generate JWT
        jwt_token = create_jwt_token(user.id)
        
        return {
            "token": jwt_token,
            "user": {
                "username": user.username,
                "avatar_url": user.avatar_url
            }
        }

@app.get("/api/user/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "avatar_url": current_user.avatar_url
    }

@app.post("/api/summarize")
async def summarize_repo(owner: str, repo: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        import json
        from models import ProjectAnalysis, Issue
        from features.feature_2_project_analysis.github_repo_fetcher import fetch_repo_metadata
        from features.feature_2_project_analysis.gemini_analyzer import analyze_project_with_gemini
        from features.feature_3_issue_analysis.gemini_issue_analyzer import sync_project_issues
        from features.feature_4_match_scoring.scoring_engine import get_or_calculate_match
        
        if not owner or not repo:
            raise HTTPException(status_code=400, detail="owner and repo are required")
            
        # 1. Fetch or create project analysis
        project = db.query(ProjectAnalysis).filter(
            ProjectAnalysis.repo_owner == owner,
            ProjectAnalysis.repo_name == repo
        ).first()
        
        if not project:
            # Quick inline project fetch and analysis
            repo_data = await fetch_repo_metadata(owner, repo)
            if not repo_data:
                raise HTTPException(status_code=404, detail=f"Failed to fetch repository data for {owner}/{repo}")
                
            ai_classification = analyze_project_with_gemini(repo_data)
            meta = repo_data['metadata']
            env = repo_data['contributor_env']
            
            last_pushed = None
            if meta.get('pushed_at'):
                try:
                    last_pushed = datetime.strptime(meta['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
                except:
                    pass
                    
            project = ProjectAnalysis(
                repo_owner=meta['owner']['login'],
                repo_name=meta['name'],
                github_repo_id=meta['id'],
                stars=meta.get('stargazers_count', 0),
                forks=meta.get('forks_count', 0),
                open_issues_count=meta.get('open_issues_count', 0),
                license=meta['license']['key'] if meta.get('license') else None,
                last_pushed_at=last_pushed,
                primary_language=meta.get('language'),
                languages_json=json.dumps(repo_data['languages']),
                has_contributing=env['has_contributing'],
                has_code_of_conduct=env['has_code_of_conduct'],
                has_issue_template=env['has_issue_template'],
                has_pr_template=env['has_pr_template'],
                architecture_type=ai_classification.architecture_type,
                platform=ai_classification.platform,
                domain_primary=ai_classification.domain_primary,
                domain_secondary=ai_classification.domain_secondary,
                health_summary=ai_classification.health_summary,
                activity_score=ai_classification.activity_score_estimate,
                beginner_score=ai_classification.beginner_score_estimate,
                last_synced_at=datetime.utcnow()
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            
        # 2. Fetch issue metadata from GitHub
        github_token = os.getenv("GITHUB_TOKEN")
        issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        headers = {"Authorization": f"token {github_token}"} if github_token else {}
        
        async with httpx.AsyncClient() as client:
            issues_res = await client.get(
                issues_url,
                headers=headers,
                params={"state": "open", "per_page": 10}
            )
            if issues_res.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch open issues from GitHub")
                
            issues_data = issues_res.json()
            github_issues = [issue for issue in issues_data if "pull_request" not in issue]
            
            # Sync / Analyze issues
            synced_issues = sync_project_issues(project, db, github_issues)

        # 3. Format issues with match scores and health ratings
        summaries = []
        for issue in synced_issues:
            score = get_or_calculate_match(current_user.id, issue.id, db)
            
            # Calculate health score dynamically matching the health report endpoint
            activity_score = project.activity_score or 50
            if project.last_pushed_at:
                days_since_push = (datetime.utcnow() - project.last_pushed_at).days
                if days_since_push <= 7:
                    push_bonus = 30
                elif days_since_push <= 30:
                    push_bonus = 15
                elif days_since_push <= 90:
                    push_bonus = 5
                else:
                    push_bonus = -20
                activity_score = max(0, min(100, activity_score + push_bonus))
            
            if project.open_issues_count == 0:
                responsiveness_score = 100
            else:
                responsiveness_score = max(30, min(100, 100 - (project.open_issues_count // 3)))
                
            beginner_score = 0
            if project.has_contributing: beginner_score += 35
            if project.has_code_of_conduct: beginner_score += 15
            if project.has_issue_template: beginner_score += 25
            if project.has_pr_template: beginner_score += 25
            
            doc_score = 30
            if project.has_contributing: doc_score += 30
            if project.has_issue_template: doc_score += 15
            if project.health_summary and len(project.health_summary) > 50:
                doc_score += 25
            doc_score = min(100, doc_score)
            
            avg_score = (activity_score + responsiveness_score + beginner_score + doc_score) / 4
            health_status = "green" if avg_score >= 75 else "amber" if avg_score >= 50 else "red"
            
            summaries.append({
                "id": issue.id,
                "project_id": project.id,
                "title": issue.issue_title,
                "url": issue.issue_url,
                "summary": issue.plain_summary or "",
                "issue_type": issue.issue_type,
                "required_skills": [s.strip() for s in issue.required_skills.split(",") if s.strip()] if issue.required_skills else [],
                "helpful_skills": [s.strip() for s in issue.helpful_skills.split(",") if s.strip()] if issue.helpful_skills else [],
                "difficulty": issue.difficulty,
                "estimated_hours": issue.estimated_hours,
                "coding_required": issue.coding_required,
                "learning_takeaways": issue.learning_takeaways,
                "match_score": score,
                "project_health_status": health_status,
                "project_health_score": int(avg_score),
                "repo_owner": project.repo_owner,
                "repo_name": project.repo_name,
                "cached": True
            })
            
        return {
            "success": True,
            "repo": f"{owner}/{repo}",
            "total_issues": len(summaries),
            "summaries": summaries
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

