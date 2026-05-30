from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User, Issue, ProjectAnalysis, DeveloperSkill
from main import get_db, get_current_user
from features.feature_8_followup_chat.gemini_chat import generate_chat_response
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ChatMessage(BaseModel):
    role: str  # "user" or "model"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]

@router.post("/api/issues/{issue_id}/chat")
async def issue_chat(
    issue_id: int,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch issue
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
        
    project = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == issue.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch user skills
    skills_objs = db.query(DeveloperSkill).filter(
        DeveloperSkill.user_id == current_user.id,
        DeveloperSkill.is_deleted == False,
        (DeveloperSkill.is_confirmed == True) | (DeveloperSkill.is_manually_added == True)
    ).all()
    user_skills_names = [s.skill_name.strip() for s in skills_objs]

    # Convert request history to simple dicts
    chat_history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]

    # Generate response
    reply = generate_chat_response(
        user=current_user,
        issue=issue,
        project=project,
        user_skills=user_skills_names,
        chat_history=chat_history_dicts,
        new_message=request.message
    )

    return {
        "reply": reply
    }
