from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import Issue, ProjectAnalysis, User, MatchScore
from main import get_db, get_current_user
from features.feature_7_ai_search.intent_parser import parse_search_intent
from features.feature_4_match_scoring.scoring_engine import get_or_calculate_match
from typing import Optional, List
from datetime import datetime

router = APIRouter()

@router.get("/api/search")
async def search_issues(
    q: Optional[str] = Query(None, description="Natural language query"),
    owner: Optional[str] = Query(None),
    repo: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    skills: Optional[str] = Query(None), # comma-separated list of skills
    max_hours: Optional[int] = Query(None),
    issue_type: Optional[str] = Query(None),
    match_by_my_skills: Optional[bool] = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Parse natural language intent if provided
    parsed_skills = []
    parsed_difficulty = difficulty
    parsed_max_hours = max_hours
    parsed_issue_type = issue_type
    parsed_coding_req = None

    if q:
        intent = parse_search_intent(q)
        parsed_skills = intent.skills
        if intent.difficulty: parsed_difficulty = intent.difficulty
        if intent.max_hours: parsed_max_hours = intent.max_hours
        if intent.issue_type: parsed_issue_type = intent.issue_type
        if intent.coding_required is not None: parsed_coding_req = intent.coding_required

    # 2. Build base query
    db_query = db.query(Issue).join(ProjectAnalysis)

    # Filter by owner/repo if specified
    if owner and repo:
        db_query = db_query.filter(
            ProjectAnalysis.repo_owner == owner,
            ProjectAnalysis.repo_name == repo
        )

    # Apply filters
    if parsed_difficulty:
        db_query = db_query.filter(Issue.difficulty == parsed_difficulty)
        
    if parsed_max_hours:
        db_query = db_query.filter(Issue.estimated_hours <= parsed_max_hours)
        
    if parsed_issue_type:
        db_query = db_query.filter(Issue.issue_type.like(f"%{parsed_issue_type}%"))
        
    if parsed_coding_req is not None:
        db_query = db_query.filter(Issue.coding_required == parsed_coding_req)

    # 3. Retrieve issues from SQLite
    issues = db_query.all()

    # 4. Filter by skills if specified (either from NLP or query params)
    skill_filter_list = []
    if skills:
        skill_filter_list = [s.strip().lower() for s in skills.split(",") if s.strip()]
    if parsed_skills:
        skill_filter_list.extend([s.lower() for s in parsed_skills])

    if skill_filter_list:
        filtered_issues = []
        for issue in issues:
            issue_skills = []
            if issue.required_skills:
                issue_skills.extend([s.strip().lower() for s in issue.required_skills.split(",")])
            if issue.helpful_skills:
                issue_skills.extend([s.strip().lower() for s in issue.helpful_skills.split(",")])
            
            # Keep issue if at least one skill matches
            if any(sf in issue_skills for sf in skill_filter_list):
                filtered_issues.append(issue)
        issues = filtered_issues

    # 5. Calculate match scores and build response list
    results = []
    for issue in issues:
        score = get_or_calculate_match(current_user.id, issue.id, db)
        
        # Get project details
        project = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == issue.project_id).first()
        
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

        results.append({
            "id": issue.id,
            "project_id": issue.project_id,
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

    # Sort by match score if match_by_my_skills is True, or if it's NLP search
    if match_by_my_skills or q:
        results = sorted(results, key=lambda x: x["match_score"], reverse=True)

    return {
        "success": True,
        "count": len(results),
        "issues": results,
        "search_parsed": {
            "skills": skill_filter_list,
            "difficulty": parsed_difficulty,
            "max_hours": parsed_max_hours,
            "issue_type": parsed_issue_type,
            "coding_required": parsed_coding_req
        }
    }
