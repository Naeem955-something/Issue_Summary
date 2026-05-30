from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User
from main import get_db, get_current_user
from pydantic import BaseModel
from typing import List
from features.feature_4_match_scoring.scoring_engine import clear_user_match_scores

router = APIRouter()

class PreferenceUpdate(BaseModel):
    availability_hours: int
    preferred_domains: List[str]

@router.get("/api/user/preferences")
async def get_preferences(current_user: User = Depends(get_current_user)):
    domains = []
    if current_user.preferred_domains:
        domains = [d.strip() for d in current_user.preferred_domains.split(",") if d.strip()]
    return {
        "availability_hours": current_user.availability_hours,
        "preferred_domains": domains
    }

@router.post("/api/user/preferences")
async def update_preferences(pref_in: PreferenceUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.availability_hours = pref_in.availability_hours
    current_user.preferred_domains = ",".join(pref_in.preferred_domains)
    db.commit()
    clear_user_match_scores(current_user.id, db)
    return {
        "message": "Preferences updated",
        "availability_hours": current_user.availability_hours,
        "preferred_domains": pref_in.preferred_domains
    }

