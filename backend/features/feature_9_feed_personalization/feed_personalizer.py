import os
import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class RerankItem(BaseModel):
    issue_id: int
    reason: str = Field(description="A short 1-sentence explanation of why this issue matches the personalization query")

class RerankResponse(BaseModel):
    ranked_items: List[RerankItem]

def rerank_feed(personalization_query: str, issues_data: list) -> list:
    """
    Uses Gemini to re-rank a list of issues based on a user's conversational prompt.
    Returns a list of dicts with {"issue_id": int, "reason": str} in the new ranked order.
    """
    if not GEMINI_API_KEY:
        # Mock fallback re-ranking
        # If query contains "easy" or "beginner", sort by difficulty: beginner first.
        # If query contains "hour" or "fast", sort by estimated hours ascending.
        # If query contains a language like "python", sort issues containing python first.
        query_lower = personalization_query.lower()
        
        def get_rank_score(issue):
            score = 0
            # language matching
            title_skills = (issue.get("title", "") + " " + " ".join(issue.get("required_skills", []))).lower()
            for lang in ["python", "react", "javascript", "fastapi", "sqlite", "css", "html"]:
                if lang in query_lower and lang in title_skills:
                    score += 50
                    
            if "easy" in query_lower or "beginner" in query_lower:
                if issue.get("difficulty") == "beginner":
                    score += 30
                elif issue.get("difficulty") == "intermediate":
                    score += 10
            elif "hard" in query_lower or "advanced" in query_lower:
                if issue.get("difficulty") == "advanced":
                    score += 30
                    
            if "fast" in query_lower or "quick" in query_lower or "short" in query_lower:
                # less hours is better
                score += max(0, 30 - issue.get("estimated_hours", 5))
                
            return score
            
        ranked = sorted(issues_data, key=get_rank_score, reverse=True)
        return [
            {
                "issue_id": item["id"],
                "reason": f"Matches query because of its {item['difficulty']} difficulty and skills: {', '.join(item['required_skills']) or 'none'}."
            }
            for item in ranked
        ]

    try:
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        
        # Format the issues list for Gemini to consume efficiently
        candidates = []
        for item in issues_data:
            candidates.append({
                "id": item["id"],
                "title": item["title"],
                "skills": item["required_skills"],
                "difficulty": item["difficulty"],
                "hours": item["estimated_hours"],
                "summary": item["summary"]
            })
            
        prompt = f"""
        Rank the following issues based on the developer's personalization request:
        "{personalization_query}"
        
        Issues list:
        {json.dumps(candidates, indent=2)}
        
        Return a JSON object ranking all the issues from most relevant to least relevant.
        Make sure you include all issues. For each issue, write a short, encouraging 1-sentence reason explaining why it fits the request.
        
        Response Format:
        {{
            "ranked_items": [
                {{
                    "issue_id": 123,
                    "reason": "This is a great python task for beginners."
                }}
            ]
        }}
        """
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=RerankResponse
            )
        )
        data = json.loads(response.text)
        return data.get("ranked_items", [])
    except Exception as e:
        print(f"Error re-ranking feed: {e}")
        return [{"issue_id": item["id"], "reason": "Standard recommendation ranking."} for item in issues_data]
