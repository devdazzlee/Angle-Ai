"""
Business Context Service - Enhanced integration with new database schema
Handles business context extraction and storage for question sequence enforcement
"""

from db.supabase import supabase
from typing import Dict, Any, Optional
import json

async def extract_and_store_business_context(session_id: str, user_id: str, tag: str, user_response: str):
    """
    Extract business context from user responses and store in session
    This ensures the AI has complete context for question sequence enforcement
    """
    
    # Get current session
    session_response = supabase.from_("chat_sessions").select("*").eq("id", session_id).eq("user_id", user_id).single().execute()
    if not session_response.data:
        return
    
    session = session_response.data
    business_context = session.get("business_context", {})
    
    # Extract context based on question tag
    updates = {}
    
    if tag == "KYC.01":  # Name
        updates["user_name"] = user_response.strip()
        business_context["user_name"] = user_response.strip()
        
    elif tag == "KYC.04":  # Work situation
        updates["employment_status"] = user_response.strip()
        business_context["employment_status"] = user_response.strip()
        
    elif tag == "KYC.05":  # Business idea
        updates["has_business_idea"] = "yes" in user_response.lower()
        business_context["has_business_idea"] = updates["has_business_idea"]
        if updates["has_business_idea"]:
            updates["business_idea_brief"] = user_response.strip()
            business_context["business_idea_brief"] = user_response.strip()
            
    elif tag == "KYC.07":  # Skills comfort level
        updates["skills_assessment"] = user_response.strip()
        business_context["skills_assessment"] = user_response.strip()
        
    elif tag == "KYC.08":  # Business type
        updates["business_type"] = user_response.strip()
        business_context["business_type"] = user_response.strip()
        
    elif tag == "KYC.09":  # Motivation
        updates["motivation"] = user_response.strip()
        business_context["motivation"] = user_response.strip()
        
    elif tag == "KYC.10":  # Location
        updates["location"] = user_response.strip()
        business_context["location"] = user_response.strip()
        
    elif tag == "KYC.11":  # Industry
        updates["industry"] = user_response.strip()
        business_context["industry"] = user_response.strip()
    
    # Add any other KYC or business plan context
    elif tag.startswith("BUSINESS_PLAN."):
        # Store business plan responses in business_context
        if "business_plan_responses" not in business_context:
            business_context["business_plan_responses"] = {}
        business_context["business_plan_responses"][tag] = user_response.strip()
    
    # Update session with extracted information
    if updates:
        updates["business_context"] = business_context
        supabase.from_("chat_sessions").update(updates).eq("id", session_id).execute()

async def get_business_context_summary(session_id: str, user_id: str) -> Dict[str, Any]:
    """Get comprehensive business context summary for AI context"""
    
    session_response = supabase.from_("chat_sessions").select("*").eq("id", session_id).eq("user_id", user_id).single().execute()
    if not session_response.data:
        return {}
    
    session = session_response.data
    
    # Build comprehensive context
    context = {
        "user_profile": {
            "name": session.get("user_name"),
            "employment_status": session.get("employment_status"),
            "location": session.get("location"),
            "industry": session.get("industry"),
            "skills_assessment": session.get("skills_assessment")
        },
        "business_concept": {
            "has_business_idea": session.get("has_business_idea"),
            "business_idea_brief": session.get("business_idea_brief"),
            "business_type": session.get("business_type"),
            "motivation": session.get("motivation")
        },
        "session_state": {
            "current_phase": session.get("current_phase"),
            "asked_q": session.get("asked_q"),
            "answered_count": session.get("answered_count")
        },
        "additional_context": session.get("business_context", {})
    }
    
    return context

async def validate_question_progression(session_id: str, user_id: str, new_tag: str) -> Dict[str, Any]:
    """
    Validate that question progression follows correct sequence
    Returns validation result with any corrections needed
    """
    
    session_response = supabase.from_("chat_sessions").select("*").eq("id", session_id).eq("user_id", user_id).single().execute()
    if not session_response.data:
        return {"valid": False, "error": "Session not found"}
    
    session = session_response.data
    current_tag = session.get("asked_q", "")
    current_phase = session.get("current_phase", "KYC")
    
    # Define expected question sequences
    QUESTION_SEQUENCES = {
        "KYC": [f"KYC.{i:02d}" for i in range(1, 20)],  # KYC.01 to KYC.19
        "BUSINESS_PLAN": [f"BUSINESS_PLAN.{i:02d}" for i in range(1, 47)],  # BUSINESS_PLAN.01 to BUSINESS_PLAN.46
        "ROADMAP": ["ROADMAP.01"],
        "IMPLEMENTATION": [f"IMPLEMENTATION.{i:02d}" for i in range(1, 11)]  # IMPLEMENTATION.01 to IMPLEMENTATION.10
    }
    
    # If no current tag, allow first question of phase
    if not current_tag:
        expected_first = QUESTION_SEQUENCES.get(current_phase, [{}])[0]
        if new_tag == expected_first:
            return {"valid": True, "corrected_tag": new_tag}
        else:
            return {"valid": False, "error": f"Expected first question {expected_first} for phase {current_phase}, got {new_tag}"}
    
    # Find current position in sequence
    phase_questions = QUESTION_SEQUENCES.get(current_phase, [])
    try:
        current_index = phase_questions.index(current_tag)
        expected_next = phase_questions[current_index + 1] if current_index + 1 < len(phase_questions) else None
        
        if new_tag == current_tag:
            # Same question - this is allowed for re-asking
            return {"valid": True, "corrected_tag": new_tag}
        elif new_tag == expected_next:
            # Correct next question
            return {"valid": True, "corrected_tag": new_tag}
        else:
            # Incorrect progression - correct it
            return {"valid": False, "corrected_tag": expected_next, "error": f"Expected next question {expected_next} after {current_tag}, got {new_tag}"}
            
    except ValueError:
        return {"valid": False, "error": f"Question {current_tag} not found in {current_phase} sequence"}

async def update_session_progress(session_id: str, user_id: str, tag: str, answered_count: int):
    """Update session progress with question sequence validation"""
    
    # Validate the tag progression
    validation = await validate_question_progression(session_id, user_id, tag)
    
    if not validation["valid"]:
        # Use corrected tag if available
        corrected_tag = validation.get("corrected_tag", tag)
        print(f"⚠️ Question sequence corrected: {tag} → {corrected_tag}")
        tag = corrected_tag
    
    # Update session with validated tag
    updates = {
        "asked_q": tag,
        "answered_count": answered_count,
        "current_phase": tag.split(".")[0]
    }
    
    supabase.from_("chat_sessions").update(updates).eq("id", session_id).execute()
    
    return {"updated_tag": tag, "validation": validation}
