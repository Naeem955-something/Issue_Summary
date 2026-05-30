from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User, Issue, MatchScore, ProjectAnalysis, DeveloperSkill
from main import get_db, get_current_user
from features.feature_4_match_scoring.scoring_engine import get_or_calculate_match
from features.feature_5_fit_explanation.gemini_explainer import generate_fit_explanation

router = APIRouter()

@router.get("/api/matches/{issue_id}/explanation")
async def get_match_explanation(issue_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Fetch issue
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
        
    project = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == issue.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Get/Calculate Score
    score = get_or_calculate_match(current_user.id, issue_id, db)
    
    # 3. Retrieve Match details
    match = db.query(MatchScore).filter(
        MatchScore.user_id == current_user.id,
        MatchScore.issue_id == issue_id
    ).first()
    
    # 4. Fetch user skills
    skills_objs = db.query(DeveloperSkill).filter(
        DeveloperSkill.user_id == current_user.id,
        DeveloperSkill.is_deleted == False,
        (DeveloperSkill.is_confirmed == True) | (DeveloperSkill.is_manually_added == True)
    ).all()
    user_skills_names = [s.skill_name.strip() for s in skills_objs]
    user_skills_lower = [s.lower() for s in user_skills_names]

    # Required and helpful skills
    req_skills = [s.strip() for s in issue.required_skills.split(",") if s.strip()] if issue.required_skills else []
    help_skills = [s.strip() for s in issue.helpful_skills.split(",") if s.strip()] if issue.helpful_skills else []
    
    matched_req = [s for s in req_skills if s.lower() in user_skills_lower]
    missing_req = [s for s in req_skills if s.lower() not in user_skills_lower]
    
    matched_help = [s for s in help_skills if s.lower() in user_skills_lower]
    missing_help = [s for s in help_skills if s.lower() not in user_skills_lower]

    # Generate Gemini Explanation if not cached
    if not match.fit_explanation:
        explanation = generate_fit_explanation(current_user, issue, project, score, user_skills_names)
        match.fit_explanation = explanation
        db.commit()
    else:
        explanation = match.fit_explanation

    # Calculate categories status
    # Learning goals
    user_goals = [g.strip() for g in current_user.learning_goals.split(",") if g.strip()] if current_user.learning_goals else []
    matched_goals = []
    takeaways_lower = (issue.learning_takeaways or "").lower()
    title_lower = (issue.issue_title or "").lower()
    issue_skills_all = {s.lower() for s in req_skills + help_skills}
    for goal in user_goals:
        if goal.lower() in issue_skills_all or goal.lower() in takeaways_lower or goal.lower() in title_lower:
            matched_goals.append(goal)

    # Domain interest
    user_domains = [d.strip() for d in current_user.preferred_domains.split(",") if d.strip()] if current_user.preferred_domains else []
    matched_domains = []
    proj_domains = []
    if project.domain_primary: proj_domains.append(project.domain_primary)
    if project.domain_secondary: proj_domains.append(project.domain_secondary)
    for ud in user_domains:
        for pd in proj_domains:
            if ud.lower() in pd.lower() or pd.lower() in ud.lower():
                matched_domains.append(ud)

    # Availability
    user_hours = current_user.availability_hours if current_user.availability_hours is not None else 10
    issue_hours = issue.estimated_hours if issue.estimated_hours is not None else 5
    availability_fit = user_hours >= issue_hours

    return {
        "issue_id": issue_id,
        "score": score,
        "explanation": explanation,
        "skills": {
            "matched_required": matched_req,
            "missing_required": missing_req,
            "matched_helpful": matched_help,
            "missing_helpful": missing_help
        },
        "learning_goals": {
            "all_goals": user_goals,
            "matched_goals": matched_goals
        },
        "domains": {
            "user_domains": user_domains,
            "project_domains": proj_domains,
            "matched_domains": matched_domains
        },
        "availability": {
            "user_hours": user_hours,
            "issue_hours": issue_hours,
            "fits": availability_fit
        },
        "project_health": {
            "activity_score": project.activity_score,
            "beginner_score": project.beginner_score,
            "health_summary": project.health_summary
        }
    }
