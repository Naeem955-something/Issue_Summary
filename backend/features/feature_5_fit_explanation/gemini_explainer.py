import os
import google.generativeai as genai
from models import User, Issue, ProjectAnalysis

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_fit_explanation(user: User, issue: Issue, project: ProjectAnalysis, score: int, user_skills: list) -> str:
    """
    Generates a 3-4 sentence plain-English fit description using Gemini.
    """
    if not GEMINI_API_KEY:
        # Mock fallback
        user_skills_str = ", ".join(user_skills) if user_skills else "none detected"
        return (
            f"You have a match score of {score}% for this issue. "
            f"Your skills in {user_skills_str} align well with the project's primary domain of {project.domain_primary}. "
            f"The estimated effort of {issue.estimated_hours} hours is within your weekly availability. "
            f"This is a great opportunity to learn {issue.learning_takeaways or 'new skills'}."
        )

    try:
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        
        prompt = f"""
        Explain why this GitHub issue is a good or challenging fit for the developer in exactly 3-4 sentences.
        Use the following details:
        
        Developer Skills: {', '.join(user_skills) if user_skills else 'None'}
        Developer Learning Goals: {user.learning_goals or 'None'}
        Developer Preferred Domains: {user.preferred_domains or 'None'}
        Developer Weekly Availability: {user.availability_hours or 10} hours
        
        Issue Title: {issue.issue_title}
        Issue Plain Summary: {issue.plain_summary}
        Issue Required Skills: {issue.required_skills or 'None'}
        Issue Helpful Skills: {issue.helpful_skills or 'None'}
        Issue Difficulty: {issue.difficulty}
        Issue Estimated Effort: {issue.estimated_hours} hours
        Issue Learning Takeaways: {issue.learning_takeaways}
        
        Project Primary Domain: {project.domain_primary}
        Project Activity Score: {project.activity_score}
        
        Match Score calculated: {score}%
        
        Provide a friendly, conversational explanation tailored directly to the developer (using "you"). Keep it concise (under 80 words) and strictly 3-4 sentences.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating fit explanation: {e}")
        return f"This issue is a {score}% match for you based on your skills and preferences. It offers a solid opportunity to contribute."
