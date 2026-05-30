import os
import google.generativeai as genai
from models import User, Issue, ProjectAnalysis

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_chat_response(
    user: User,
    issue: Issue,
    project: ProjectAnalysis,
    user_skills: list,
    chat_history: list,
    new_message: str
) -> str:
    """
    Answers a follow-up developer question about an issue using Gemini.
    """
    if not GEMINI_API_KEY:
        # Mock fallback response
        new_msg_lower = new_message.lower()
        if "start" in new_msg_lower or "where" in new_msg_lower or "file" in new_msg_lower:
            return (
                f"To get started on this issue ({issue.issue_title}), you should look at the primary repository "
                f"structure. Since the project primary language is {project.primary_language}, look for "
                f"relevant files in the source directories. Let me know if you need help finding specific methods!"
            )
        elif "skill" in new_msg_lower or "learn" in new_msg_lower:
            return (
                f"Contributing to this issue will help you build skills in: {issue.required_skills}. "
                f"This perfectly aligns with your learning goals: {user.learning_goals or 'general growth'}."
            )
        else:
            return (
                f"I'm in mock mode, but here is some guidance on '{new_message}': "
                f"Make sure to read the README and CONTRIBUTING.md files of {project.repo_owner}/{project.repo_name}. "
                f"This issue has an estimated effort of {issue.estimated_hours} hours. "
                f"Let me know what specific questions you have about the codebase!"
            )

    try:
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        
        # Build the conversation history string
        history_str = ""
        for msg in chat_history:
            role = "Developer" if msg.get("role") == "user" else "AI Assistant"
            history_str += f"{role}: {msg.get('content')}\n"
            
        prompt = f"""
        You are DevCollab AI, an expert technical mentor helping a developer understand a GitHub issue and how to start working on it.
        
        Context details:
        Developer profile:
        - Skills: {', '.join(user_skills) if user_skills else 'None'}
        - Learning Goals: {user.learning_goals or 'None'}
        - Preferred Domains: {user.preferred_domains or 'None'}
        
        Project info:
        - Repository: {project.repo_owner}/{project.repo_name}
        - Domain: {project.domain_primary}
        - Architecture: {project.architecture_type}
        - Primary Language: {project.primary_language}
        - Health summary: {project.health_summary}
        
        Issue details:
        - Title: {issue.issue_title}
        - Plain summary: {issue.plain_summary}
        - Required skills: {issue.required_skills}
        - Helpful skills: {issue.helpful_skills}
        - Estimated effort: {issue.estimated_hours} hours
        - Learning takeaways: {issue.learning_takeaways}
        
        Conversation History:
        {history_str}
        
        Developer: "{new_message}"
        
        Provide a detailed, helpful, and concise response (150 words or less). Focus on technical guidance, files to look at, or skills required. If they ask how to get started, give them 2-3 logical first steps based on the language and architecture. Maintain a warm, encouraging mentoring tone.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error in Gemini chat: {e}")
        return "I encountered an error trying to process your question. Please try again in a moment."
