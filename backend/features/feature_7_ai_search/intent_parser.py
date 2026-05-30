import os
import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class SearchIntent(BaseModel):
    skills: List[str] = Field(description="Skills mentioned in the search query, e.g., ['python', 'react']")
    difficulty: Optional[str] = Field(description="beginner, intermediate, or advanced")
    max_hours: Optional[int] = Field(description="Maximum estimated hours if mentioned")
    issue_type: Optional[str] = Field(description="bug fix, new feature, documentation, refactoring, testing, etc.")
    coding_required: Optional[bool] = Field(description="Whether coding is required (e.g. documentation is false)")

def parse_search_intent(query: str) -> SearchIntent:
    """
    Parses a natural language search query into structured search parameters using Gemini.
    """
    if not GEMINI_API_KEY:
        # Mock fallback parsing
        query_lower = query.lower()
        skills = []
        for s in ["python", "javascript", "react", "fastapi", "sqlite", "css", "html", "git", "c++", "rust"]:
            if s in query_lower:
                skills.append(s)
        
        difficulty = None
        if "easy" in query_lower or "beginner" in query_lower or "first" in query_lower:
            difficulty = "beginner"
        elif "hard" in query_lower or "advanced" in query_lower or "expert" in query_lower:
            difficulty = "advanced"
        elif "medium" in query_lower or "intermediate" in query_lower:
            difficulty = "intermediate"
            
        max_hours = None
        if "hour" in query_lower:
            # Try to extract a number before "hour"
            import re
            match = re.search(r'(\d+)\s*hour', query_lower)
            if match:
                max_hours = int(match.group(1))

        issue_type = None
        if "bug" in query_lower or "fix" in query_lower:
            issue_type = "bug fix"
        elif "feature" in query_lower or "add" in query_lower:
            issue_type = "new feature"
        elif "doc" in query_lower or "readme" in query_lower:
            issue_type = "documentation"
            
        return SearchIntent(
            skills=skills,
            difficulty=difficulty,
            max_hours=max_hours,
            issue_type=issue_type,
            coding_required=False if "doc" in query_lower or "design" in query_lower else None
        )

    try:
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        
        prompt = f"""
        Extract structured search parameters from this natural language query for GitHub issues.
        
        Query: "{query}"
        
        Return a JSON object matching this schema:
        {{
            "skills": ["python", "react"],
            "difficulty": "beginner | intermediate | advanced | null",
            "max_hours": 5 | null,
            "issue_type": "bug fix | new feature | documentation | testing | null",
            "coding_required": true | false | null
        }}
        """
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=SearchIntent
            )
        )
        return SearchIntent.model_validate_json(response.text)
    except Exception as e:
        print(f"Error parsing search intent: {e}")
        return SearchIntent(skills=[], difficulty=None, max_hours=None, issue_type=None, coding_required=None)
