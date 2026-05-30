from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import ProjectAnalysis, User
from main import get_db, get_current_user
from datetime import datetime

router = APIRouter()

@router.get("/api/projects/{project_id}/health-report")
async def get_project_health_report(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 1. Activity Score (0-100)
    # Based on stars, forks, and last push time
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

    # 2. Responsiveness Score (0-100)
    # Estimate responsiveness based on open issues count relative to stars
    if project.open_issues_count == 0:
        responsiveness_score = 100
    else:
        # A simple logic: if open issues count is low, responsiveness is higher
        responsiveness_score = max(30, min(100, 100 - (project.open_issues_count // 3)))

    # 3. Beginner Friendliness Score (0-100)
    # Calculated from contribution environment files
    beginner_score = 0
    if project.has_contributing: beginner_score += 35
    if project.has_code_of_conduct: beginner_score += 15
    if project.has_issue_template: beginner_score += 25
    if project.has_pr_template: beginner_score += 25
    
    # 4. Documentation Score (0-100)
    # Check README length (simulated or based on files)
    doc_score = 30
    if project.has_contributing: doc_score += 30
    if project.has_issue_template: doc_score += 15
    # If the database has a health summary (meaning we had README context), add to docs score
    if project.health_summary and len(project.health_summary) > 50:
        doc_score += 25
    doc_score = min(100, doc_score)

    # Health rating label: Green, Amber, Red
    avg_score = (activity_score + responsiveness_score + beginner_score + doc_score) / 4
    if avg_score >= 75:
        rating = "green"
    elif avg_score >= 50:
        rating = "amber"
    else:
        rating = "red"

    return {
        "project_id": project.id,
        "repo_owner": project.repo_owner,
        "repo_name": project.repo_name,
        "overall_rating": rating,
        "average_score": int(avg_score),
        "sub_scores": {
            "activity": activity_score,
            "responsiveness": responsiveness_score,
            "beginner_friendliness": beginner_score,
            "documentation": doc_score
        },
        "health_summary": project.health_summary or "No health summary available for this project. Try re-syncing the project details."
    }
