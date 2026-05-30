from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User
from main import get_db, get_current_user
from features.feature_9_feed_personalization.feed_personalizer import rerank_feed
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class IssueInput(BaseModel):
    id: int
    title: str
    summary: str
    difficulty: str
    estimated_hours: Optional[float] = None
    required_skills: List[str]
    helpful_skills: List[str]
    # Extra fields to preserve
    project_id: Optional[int] = None
    url: Optional[str] = None
    issue_type: Optional[str] = None
    coding_required: Optional[bool] = None
    learning_takeaways: Optional[str] = None
    match_score: Optional[float] = None
    project_health_status: Optional[str] = None
    project_health_score: Optional[int] = None
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    cached: Optional[bool] = None

class PersonalizeRequest(BaseModel):
    query: str
    issues: List[IssueInput]

@router.post("/api/feed/personalize")
async def personalize_feed(
    request: PersonalizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not request.query.strip():
        return {"ranked_issues": [issue.model_dump() for issue in request.issues], "suggested_goals": []}

    # Convert request issues to simple list of dicts
    issues_data = []
    for issue in request.issues:
        issues_data.append({
            "id": issue.id,
            "title": issue.title,
            "summary": issue.summary,
            "difficulty": issue.difficulty,
            "estimated_hours": issue.estimated_hours,
            "required_skills": issue.required_skills,
            "helpful_skills": issue.helpful_skills
        })

    # Get ranking from Gemini/mock helper
    ranked_results = rerank_feed(request.query, issues_data)

    # Re-order the original issues list according to the ranked_results
    ranking_map = {item["issue_id"]: (idx, item["reason"]) for idx, item in enumerate(ranked_results)}
    
    # Check which issues are in the ranking map and sort them
    ranked_issues = []
    for issue in request.issues:
        if issue.id in ranking_map:
            idx, reason = ranking_map[issue.id]
            issue_dict = issue.model_dump()
            issue_dict["personalization_reason"] = reason
            ranked_issues.append((idx, issue_dict))
        else:
            # Fallback for issues not returned in list
            issue_dict = issue.model_dump()
            issue_dict["personalization_reason"] = "Standard match recommendation."
            ranked_issues.append((len(ranked_results), issue_dict))
            
    ranked_issues = [item[1] for item in sorted(ranked_issues, key=lambda x: x[0])]

    # Extract potential learning goals from user's personalization query
    # E.g. if user mentions a programming language/framework, offer it as a chip
    potential_goals = []
    query_lower = request.query.lower()
    known_skills = ["react", "python", "javascript", "typescript", "fastapi", "sqlite", "css", "html", "docker", "kubernetes", "aws", "git", "rust", "go", "c++", "java"]
    
    # Check existing user goals to avoid duplicates
    existing_goals = [g.strip().lower() for g in current_user.learning_goals.split(",") if g.strip()] if current_user.learning_goals else []
    
    for skill in known_skills:
        if skill in query_lower and skill not in existing_goals:
            potential_goals.append(skill.title())

    return {
        "ranked_issues": ranked_issues,
        "suggested_goals": potential_goals
    }
