import os
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class SkillItem(BaseModel):
    skill_name: str
    proficiency: str = Field(description="'beginner', 'intermediate', or 'advanced'")
    source: str = Field(description="Short phrase explaining evidence, e.g., 'found in dependency file across 6 repos'")

class DeveloperSkillProfile(BaseModel):
    languages_and_ecosystems: List[SkillItem]
    frameworks_and_libraries: List[SkillItem]
    tools_and_infrastructure: List[SkillItem]
    domain_expertise: List[SkillItem]

def extract_skills_from_context(github_context: str) -> DeveloperSkillProfile:
    """Uses Gemini to extract structured developer skills from raw GitHub file context."""
    if not GEMINI_API_KEY:
        # Mock response for testing if no key
        return DeveloperSkillProfile(
            languages_and_ecosystems=[SkillItem(skill_name="Python", proficiency="intermediate", source="Mock inference")],
            frameworks_and_libraries=[],
            tools_and_infrastructure=[],
            domain_expertise=[]
        )
        
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
    Analyze the following raw file contents and directory listings from a developer's GitHub repositories.
    Extract the developer's skills and return them as a structured JSON object.
    
    Rules for proficiency:
    - 'beginner': Only mentioned briefly or used in simple contexts.
    - 'intermediate': Used across multiple files/repos or standard usage.
    - 'advanced': Dominant language, complex configurations, or custom tooling detected.
    
    Provide a 'source' phrase indicating exactly why you inferred this skill.
    Infer everything from the context; do not hallucinate skills.
    
    Context:
    {github_context}
    """
    
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=DeveloperSkillProfile,
        )
    )
    
    # Parse the json response into our pydantic model
    return DeveloperSkillProfile.model_validate_json(response.text)
