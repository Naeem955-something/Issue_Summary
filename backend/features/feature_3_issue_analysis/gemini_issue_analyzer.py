import os
import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List

# Define the structured output model using Pydantic
class IssueAnalysisOutput(BaseModel):
    issue_type: str = Field(description="One of: bug fix, new feature, documentation, refactoring, testing, performance, security, design/UX, community, translation, accessibility")
    plain_summary: str = Field(description="3-sentence summary: What is the problem? What needs to be done? Who is suitable?")
    required_skills: List[str] = Field(description="Skills without which you cannot do this task")
    helpful_skills: List[str] = Field(description="Skills that make it easier but are not essential")
    difficulty: str = Field(description="beginner, intermediate, or advanced")
    estimated_hours: int = Field(description="Estimated hours to complete the task")
    coding_required: bool = Field(description="Whether coding is required (documentation or design are false)")
    learning_takeaways: str = Field(description="What the contributor will learn from completing this task")

def analyze_issue_with_gemini(title: str, body: str, project_context_str: str) -> IssueAnalysisOutput:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Mock fallback for keyless environments
        return IssueAnalysisOutput(
            issue_type="bug fix",
            plain_summary=f"Mock summary of issue: {title}. Requires fixing the root cause. Suitable for intermediate developers.",
            required_skills=["Python", "git"],
            helpful_skills=["FastAPI", "SQLite"],
            difficulty="intermediate",
            estimated_hours=4,
            coding_required=True,
            learning_takeaways="How to debug routing and manage database connections in Python."
        )

    try:
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        
        # Configure model to return structured JSON adhering to the Pydantic schema
        model = genai.GenerativeModel(
            model_name,
            generation_config={"response_mime_type": "application/json"}
        )
        
        prompt = f"""
        Analyze this GitHub issue and return a structured JSON object.
        Use the project context to infer implicit details. For instance, if the project is a React app,
        any UI issue implicitly requires React/Javascript, even if not stated in the issue.

        Project Context:
        {project_context_str}

        GitHub Issue Title: {title}
        GitHub Issue Body:
        {body}

        Return JSON matching this schema:
        {{
            "issue_type": "bug fix | new feature | documentation | refactoring | testing | performance | security | design/UX | community | translation | accessibility",
            "plain_summary": "three sentence summary explaining the problem, the solution, and who is suitable",
            "required_skills": ["skill1", "skill2"],
            "helpful_skills": ["skill1", "skill2"],
            "difficulty": "beginner | intermediate | advanced",
            "estimated_hours": 5,
            "coding_required": true,
            "learning_takeaways": "detailed explanation of learning outcomes"
        }}
        """
        
        response = model.generate_content(prompt)
        data = json.loads(response.text)
        return IssueAnalysisOutput(**data)
        
    except Exception as e:
        print(f"Error during Gemini issue analysis: {e}")
        # Return fallback on error
        return IssueAnalysisOutput(
            issue_type="bug fix",
            plain_summary=f"Error analyzing issue: {title}. Please check system configurations.",
            required_skills=[],
            helpful_skills=[],
            difficulty="intermediate",
            estimated_hours=2,
            coding_required=True,
            learning_takeaways="N/A"
        )

def sync_project_issues(project, db, github_issues: list):
    """
    Analyzes and saves open issues for a given ProjectAnalysis in the database.
    """
    from models import Issue
    import json
    
    project_context_str = (
        f"Primary language: {project.primary_language}. "
        f"Description: {project.health_summary or ''}. "
        f"Domains: {project.domain_primary or ''}, {project.domain_secondary or ''}. "
        f"Architecture: {project.architecture_type or ''}."
    )
    
    synced_issues = []
    for g_issue in github_issues:
        # Check if already exists in DB
        db_issue = db.query(Issue).filter(Issue.github_issue_id == g_issue['id']).first()
        
        if not db_issue:
            analysis = analyze_issue_with_gemini(
                title=g_issue['title'],
                body=g_issue.get('body') or '',
                project_context_str=project_context_str
            )
            
            db_issue = Issue(
                project_id=project.id,
                github_issue_id=g_issue['id'],
                issue_title=g_issue['title'],
                issue_url=g_issue['html_url'],
                issue_type=analysis.issue_type,
                plain_summary=analysis.plain_summary,
                required_skills=",".join(analysis.required_skills),
                helpful_skills=",".join(analysis.helpful_skills),
                difficulty=analysis.difficulty,
                estimated_hours=analysis.estimated_hours,
                coding_required=analysis.coding_required,
                learning_takeaways=analysis.learning_takeaways
            )
            db.add(db_issue)
            db.commit()
            db.refresh(db_issue)
            
        synced_issues.append(db_issue)
        
    return synced_issues

