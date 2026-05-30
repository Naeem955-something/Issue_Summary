from sqlalchemy.orm import Session
from models import User, Issue, ProjectAnalysis, DeveloperSkill, MatchScore
from datetime import datetime

def calculate_match_score(user: User, issue: Issue, project: ProjectAnalysis, db: Session) -> int:
    """
    Calculates a match score (0-100) between a User and an Issue using the 5-component formula:
    1. Skill Coverage (40%)
    2. Learning Goals (20%)
    3. Domain Interest (15%)
    4. Availability vs Effort (15%)
    5. Project Health (10%)
    """
    # 1. Fetch User Skills (confirmed or manual)
    user_skills_objs = db.query(DeveloperSkill).filter(
        DeveloperSkill.user_id == user.id,
        DeveloperSkill.is_deleted == False,
        (DeveloperSkill.is_confirmed == True) | (DeveloperSkill.is_manually_added == True)
    ).all()
    user_skills = {s.skill_name.strip().lower() for s in user_skills_objs}

    # Issue Skills
    req_skills_list = [s.strip().lower() for s in issue.required_skills.split(",") if s.strip()] if issue.required_skills else []
    help_skills_list = [s.strip().lower() for s in issue.helpful_skills.split(",") if s.strip()] if issue.helpful_skills else []

    # Calculate Skill Coverage (40%)
    if not req_skills_list and not help_skills_list:
        skill_coverage_score = 100
    else:
        req_matched = [s for s in req_skills_list if s in user_skills]
        help_matched = [s for s in help_skills_list if s in user_skills]
        
        req_fraction = len(req_matched) / len(req_skills_list) if req_skills_list else 1.0
        help_fraction = len(help_matched) / len(help_skills_list) if help_skills_list else 1.0
        
        if req_skills_list and help_skills_list:
            skill_coverage_score = int((0.8 * req_fraction + 0.2 * help_fraction) * 100)
        elif req_skills_list:
            skill_coverage_score = int(req_fraction * 100)
        else:
            skill_coverage_score = int(help_fraction * 100)

    # 2. Learning Goals (20%)
    user_goals = [g.strip().lower() for g in user.learning_goals.split(",") if g.strip()] if user.learning_goals else []
    if not user_goals:
        learning_goals_score = 50  # Neutral score if no goals defined
    else:
        # Check if any learning goal matches issue required/helpful skills or learning takeaways keywords
        matched_goals = 0
        takeaways_lower = (issue.learning_takeaways or "").lower()
        title_lower = (issue.issue_title or "").lower()
        issue_skills_all = set(req_skills_list + help_skills_list)
        
        for goal in user_goals:
            if goal in issue_skills_all or goal in takeaways_lower or goal in title_lower:
                matched_goals += 1
                
        if matched_goals >= 1:
            learning_goals_score = 100
        else:
            learning_goals_score = 0

    # 3. Domain Interest (15%)
    user_domains = [d.strip().lower() for d in user.preferred_domains.split(",") if d.strip()] if user.preferred_domains else []
    if not user_domains:
        domain_interest_score = 50  # Neutral
    else:
        proj_domains = []
        if project.domain_primary: proj_domains.append(project.domain_primary.lower())
        if project.domain_secondary: proj_domains.append(project.domain_secondary.lower())
        
        # Check if primary or secondary domain matches any preferred domain
        matched = False
        for ud in user_domains:
            for pd in proj_domains:
                if ud in pd or pd in ud:
                    matched = True
                    break
        domain_interest_score = 100 if matched else 0

    # 4. Availability vs Effort (15%)
    user_hours = user.availability_hours if user.availability_hours is not None else 10
    issue_hours = issue.estimated_hours if issue.estimated_hours is not None else 5
    
    if user_hours >= issue_hours:
        availability_score = 100
    else:
        availability_score = max(0, 100 - (issue_hours - user_hours) * 10)

    # 5. Project Health (10%)
    project_health_score = project.activity_score if project.activity_score is not None else 50

    # Weighted calculation
    final_score = int(
        0.40 * skill_coverage_score +
        0.20 * learning_goals_score +
        0.15 * domain_interest_score +
        0.15 * availability_score +
        0.10 * project_health_score
    )

    # Make sure it is capped between 0 and 100
    return max(0, min(100, final_score))

def get_or_calculate_match(user_id: int, issue_id: int, db: Session) -> int:
    """Retrieves or calculates and persists a match score."""
    match = db.query(MatchScore).filter(
        MatchScore.user_id == user_id,
        MatchScore.issue_id == issue_id
    ).first()

    if match:
        return match.score

    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not issue or not user:
        return 0

    project = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == issue.project_id).first()
    if not project:
        return 0

    score_val = calculate_match_score(user, issue, project, db)
    
    match = MatchScore(
        user_id=user_id,
        issue_id=issue_id,
        score=score_val,
        last_calculated_at=datetime.utcnow()
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match.score

def clear_user_match_scores(user_id: int, db: Session):
    """Deletes all match score cache records for a user when their skills or preferences change."""
    db.query(MatchScore).filter(MatchScore.user_id == user_id).delete()
    db.commit()

