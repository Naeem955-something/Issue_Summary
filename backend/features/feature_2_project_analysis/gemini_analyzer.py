import os
import google.generativeai as genai
from pydantic import BaseModel, Field

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class ProjectClassification(BaseModel):
    architecture_type: str = Field(description="'monolith', 'microservices', 'cli', 'library', 'framework'")
    platform: str = Field(description="'web', 'mobile', 'desktop', 'backend', 'cross-platform'")
    domain_primary: str = Field(description="Primary domain e.g., 'Web Development', 'DevOps', 'Data Science'")
    domain_secondary: str = Field(description="Secondary domain if applicable")
    health_summary: str = Field(description="One honest paragraph summarizing whether this project is worth a contributor's time based on activity and docs.")
    activity_score_estimate: int = Field(description="0-100 score estimating project health based on recent pushes, issues, and PR stats.")
    beginner_score_estimate: int = Field(description="0-100 score estimating beginner friendliness based on presence of guides and templates.")

def analyze_project_with_gemini(repo_data: dict) -> ProjectClassification:
    """Uses Gemini to classify the project domain, architecture, and generate a health report."""
    if not GEMINI_API_KEY:
        return ProjectClassification(
            architecture_type="library", platform="backend", 
            domain_primary="Tooling", domain_secondary="Utility", 
            health_summary="Mock summary (API Key missing).",
            activity_score_estimate=50, beginner_score_estimate=50
        )
        
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # Construct a context blob
    meta = repo_data['metadata']
    context = f"""
    Repository: {meta['full_name']}
    Description: {meta['description']}
    Stars: {meta['stargazers_count']}
    Forks: {meta['forks_count']}
    Open Issues: {meta['open_issues_count']}
    Created: {meta['created_at']}
    Last Pushed: {meta['pushed_at']}
    Primary Language: {meta['language']}
    Languages: {repo_data['languages']}
    
    Contributor Environment:
    Has Contributing.md: {repo_data['contributor_env']['has_contributing']}
    Has Code of Conduct: {repo_data['contributor_env']['has_code_of_conduct']}
    Has Issue Templates: {repo_data['contributor_env']['has_issue_template']}
    
    README Snippet:
    {repo_data['readme']}
    """
    
    prompt = f"""
    Based on the following repository metadata and README snippet, analyze this project.
    Provide a structured classification of its architecture, platform, and domain.
    Also generate a project health report paragraph explaining if this is a good, active project for a newcomer to contribute to right now.
    
    Context:
    {context}
    """
    
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=ProjectClassification,
        )
    )
    
    return ProjectClassification.model_validate_json(response.text)
