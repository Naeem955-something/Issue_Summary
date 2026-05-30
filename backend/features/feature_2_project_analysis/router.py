from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from models import ProjectAnalysis, User
from main import get_db, get_current_user
from features.feature_2_project_analysis.github_repo_fetcher import fetch_repo_metadata
from features.feature_2_project_analysis.gemini_analyzer import analyze_project_with_gemini
from datetime import datetime
import json

router = APIRouter()

async def sync_project_analysis_task(owner: str, repo: str):
    from main import SessionLocal
    db = SessionLocal()
    try:
        # Fetch GitHub data
        repo_data = await fetch_repo_metadata(owner, repo)
        if not repo_data:
            print(f"Failed to fetch data for {owner}/{repo}")
            return
            
        # Get AI Classification
        ai_classification = analyze_project_with_gemini(repo_data)
        meta = repo_data['metadata']
        env = repo_data['contributor_env']
        
        # Check if project exists by owner & repo name (so placeholder works)
        project = db.query(ProjectAnalysis).filter(
            ProjectAnalysis.repo_owner == owner,
            ProjectAnalysis.repo_name == repo
        ).first()
        
        # We need datetime objects
        last_pushed = None
        if meta.get('pushed_at'):
            try:
                last_pushed = datetime.strptime(meta['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
            except:
                pass
            
        if not project:
            project = ProjectAnalysis(
                repo_owner=owner,
                repo_name=repo,
                github_repo_id=meta['id']
            )
            db.add(project)
            
        # Update attributes
        project.github_repo_id = meta['id']
        project.stars = meta.get('stargazers_count', 0)
        project.forks = meta.get('forks_count', 0)
        project.open_issues_count = meta.get('open_issues_count', 0)
        project.license = meta['license']['key'] if meta.get('license') else None
        project.last_pushed_at = last_pushed
        project.primary_language = meta.get('language')
        project.languages_json = json.dumps(repo_data['languages'])
        
        project.has_contributing = env['has_contributing']
        project.has_code_of_conduct = env['has_code_of_conduct']
        project.has_issue_template = env['has_issue_template']
        project.has_pr_template = env['has_pr_template']
        
        project.architecture_type = ai_classification.architecture_type
        project.platform = ai_classification.platform
        project.domain_primary = ai_classification.domain_primary
        project.domain_secondary = ai_classification.domain_secondary
        project.health_summary = ai_classification.health_summary
        project.activity_score = ai_classification.activity_score_estimate
        project.beginner_score = ai_classification.beginner_score_estimate
        project.last_synced_at = datetime.utcnow()
        
        db.commit()
        db.refresh(project)

        # Fetch and sync issues in background
        import httpx
        from features.feature_3_issue_analysis.gemini_issue_analyzer import sync_project_issues
        import os
        
        github_token = os.getenv("GITHUB_TOKEN")
        issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        headers = {"Authorization": f"token {github_token}"} if github_token else {}
        
        async with httpx.AsyncClient() as client:
            issues_res = await client.get(
                issues_url,
                headers=headers,
                params={"state": "open", "per_page": 10}
            )
            if issues_res.status_code == 200:
                issues_data = issues_res.json()
                github_issues = [issue for issue in issues_data if "pull_request" not in issue]
                sync_project_issues(project, db, github_issues)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error syncing project {owner}/{repo}: {str(e)}")
    finally:
        db.close()


@router.post("/api/projects/register")
async def register_project(owner: str, repo: str, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Registers a repository and triggers background AI analysis."""
    
    # Check if already exists
    existing = db.query(ProjectAnalysis).filter(
        ProjectAnalysis.repo_owner == owner,
        ProjectAnalysis.repo_name == repo
    ).first()
    
    if existing:
        background_tasks.add_task(sync_project_analysis_task, owner, repo)
        return {"message": "Project already registered. Re-sync triggered.", "project_id": existing.id}
        
    # Create placeholder entry to return project_id immediately
    new_project = ProjectAnalysis(
        repo_owner=owner,
        repo_name=repo,
        stars=0,
        forks=0,
        open_issues_count=0
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    background_tasks.add_task(sync_project_analysis_task, owner, repo)
    return {"message": f"Project {owner}/{repo} registered for background analysis.", "project_id": new_project.id}

@router.get("/api/projects/{project_id}")
async def get_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
