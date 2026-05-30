from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from models import DeveloperSkill, User
from main import get_db, get_current_user
from features.feature_1_skill_profile.github_parser import analyze_user_github_context
from features.feature_1_skill_profile.gemini_extractor import extract_skills_from_context
from datetime import datetime
from pydantic import BaseModel
from typing import List
from features.feature_4_match_scoring.scoring_engine import clear_user_match_scores

router = APIRouter()

class ManualSkillCreate(BaseModel):
    skill_name: str
    category: str
    proficiency: str

class LearningGoalsUpdate(BaseModel):
    learning_goals: List[str]

async def sync_developer_skills_task(user_id: int, github_username: str):
    from main import SessionLocal
    db = SessionLocal()
    try:
        # 1. Fetch Context
        context = await analyze_user_github_context(github_username)
        
        # 2. Extract Skills using Gemini
        profile_data = extract_skills_from_context(context)
        
        # 3. Save to Database
        categories = {
            "languages_and_ecosystems": profile_data.languages_and_ecosystems,
            "frameworks_and_libraries": profile_data.frameworks_and_libraries,
            "tools_and_infrastructure": profile_data.tools_and_infrastructure,
            "domain_expertise": profile_data.domain_expertise
        }
        
        new_skills_added = False
        for category, skills in categories.items():
            for skill in skills:
                # Check if skill exists and is not deleted
                existing = db.query(DeveloperSkill).filter(
                    DeveloperSkill.user_id == user_id,
                    DeveloperSkill.skill_name == skill.skill_name,
                    DeveloperSkill.category == category
                ).first()
                
                if existing:
                    if not existing.is_deleted and not existing.is_manually_added:
                        existing.last_detected_at = datetime.utcnow()
                        existing.proficiency = skill.proficiency
                        existing.source = skill.source
                else:
                    new_skill = DeveloperSkill(
                        user_id=user_id,
                        skill_name=skill.skill_name,
                        category=category,
                        proficiency=skill.proficiency,
                        source=skill.source,
                        is_confirmed=False
                    )
                    db.add(new_skill)
                    new_skills_added = True
                    
        if new_skills_added:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.new_skills_detected = True
        db.commit()
        clear_user_match_scores(user_id, db)
    except Exception as e:
        db.rollback()
        print(f"Error syncing skills for user {user_id}: {str(e)}")
    finally:
        db.close()

@router.post("/api/user/sync-skills")
async def trigger_skill_sync(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Triggers an asynchronous skill scan across user's public repos."""
    
    if not current_user.username:
        raise HTTPException(status_code=400, detail="GitHub username not found on user profile")
        
    background_tasks.add_task(sync_developer_skills_task, current_user.id, current_user.username)
    return {"message": "Skill synchronization started in background"}

@router.get("/api/user/skills")
async def get_user_skills(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch all non-deleted skills grouped by category, showing unconfirmed banner state."""
    skills = db.query(DeveloperSkill).filter(
        DeveloperSkill.user_id == current_user.id,
        DeveloperSkill.is_deleted == False
    ).all()
    
    grouped = {
        "languages_and_ecosystems": [],
        "frameworks_and_libraries": [],
        "tools_and_infrastructure": [],
        "domain_expertise": [],
        "new_skills_detected": current_user.new_skills_detected
    }
    
    for s in skills:
        if s.category in grouped:
            grouped[s.category].append({
                "id": s.id,
                "skill_name": s.skill_name,
                "proficiency": s.proficiency,
                "source": s.source,
                "is_confirmed": s.is_confirmed,
                "is_manually_added": s.is_manually_added
            })
            
    return grouped

@router.post("/api/user/skills")
async def add_manual_skill(skill_in: ManualSkillCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Manually add a skill with is_manually_added=True and is_confirmed=True."""
    valid_categories = ["languages_and_ecosystems", "frameworks_and_libraries", "tools_and_infrastructure", "domain_expertise"]
    if skill_in.category not in valid_categories:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    # Check if skill already exists (even if deleted)
    existing = db.query(DeveloperSkill).filter(
        DeveloperSkill.user_id == current_user.id,
        DeveloperSkill.skill_name == skill_in.skill_name,
        DeveloperSkill.category == skill_in.category
    ).first()
    
    if existing:
        if existing.is_deleted:
            existing.is_deleted = False
            existing.is_manually_added = True
            existing.is_confirmed = True
            existing.proficiency = skill_in.proficiency
            existing.source = "Manually added by developer"
            db.commit()
            clear_user_match_scores(current_user.id, db)
            return {"message": "Skill added", "id": existing.id}
        else:
            raise HTTPException(status_code=400, detail="Skill already exists in this category")
            
    new_skill = DeveloperSkill(
        user_id=current_user.id,
        skill_name=skill_in.skill_name,
        category=skill_in.category,
        proficiency=skill_in.proficiency,
        source="Manually added by developer",
        is_confirmed=True,
        is_manually_added=True
    )
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    clear_user_match_scores(current_user.id, db)
    return {"message": "Skill added", "id": new_skill.id}

@router.post("/api/user/skills/confirm/{skill_id}")
async def confirm_skill(skill_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Confirms an auto-detected skill."""
    skill = db.query(DeveloperSkill).filter(
        DeveloperSkill.id == skill_id,
        DeveloperSkill.user_id == current_user.id
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill.is_confirmed = True
    db.commit()
    clear_user_match_scores(current_user.id, db)
    return {"message": "Skill confirmed"}

@router.delete("/api/user/skills/{skill_id}")
async def remove_skill(skill_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Soft deletes a detected skill."""
    skill = db.query(DeveloperSkill).filter(
        DeveloperSkill.id == skill_id,
        DeveloperSkill.user_id == current_user.id
    ).first()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
        
    skill.is_deleted = True
    db.commit()
    clear_user_match_scores(current_user.id, db)
    return {"message": "Skill removed"}

@router.get("/api/user/learning-goals")
async def get_learning_goals(current_user: User = Depends(get_current_user)):
    """Gets the developer's learning goals."""
    goals = []
    if current_user.learning_goals:
        goals = [g.strip() for g in current_user.learning_goals.split(",") if g.strip()]
    return {"learning_goals": goals}

@router.post("/api/user/learning-goals")
async def update_learning_goals(goals_in: LearningGoalsUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Updates the developer's learning goals."""
    current_user.learning_goals = ",".join(goals_in.learning_goals)
    db.commit()
    clear_user_match_scores(current_user.id, db)
    return {"message": "Learning goals updated", "learning_goals": goals_in.learning_goals}

@router.post("/api/user/clear-new-skills-banner")
async def clear_new_skills_banner(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Clears the new skills notification banner flag."""
    current_user.new_skills_detected = False
    db.commit()
    return {"message": "Banner cleared"}
