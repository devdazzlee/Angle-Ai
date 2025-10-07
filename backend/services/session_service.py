from db.supabase import supabase

async def create_session(user_id: str, title: str):
    response = supabase \
        .from_("chat_sessions") \
        .insert({
            "user_id": user_id, 
            "title": title,
            "current_phase": "KYC",
            "asked_q": "KYC.01",
            "answered_count": 0
        }) \
        .execute()

    if response.data:
        return response.data[0]
    else:
        raise Exception("Failed to create session")

async def list_sessions(user_id: str):
    response = supabase.from_("chat_sessions").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
    return response.data

async def get_session(session_id: str, user_id: str):
    response = supabase.from_("chat_sessions").select("*").eq("id", session_id).eq("user_id", user_id).single().execute()
    
    if response.data:
        session = response.data
        # Ensure session has required fields with defaults
        session.setdefault("current_phase", "KYC")
        session.setdefault("asked_q", "KYC.01")
        session.setdefault("answered_count", 0)
        session.setdefault("business_context", {})
        session.setdefault("roadmap_data", None)
        session.setdefault("implementation_data", None)
        session.setdefault("user_name", None)
        session.setdefault("employment_status", None)
        session.setdefault("has_business_idea", None)
        session.setdefault("business_idea_brief", None)
        session.setdefault("business_type", None)
        session.setdefault("motivation", None)
        session.setdefault("location", None)
        session.setdefault("industry", None)
        session.setdefault("skills_assessment", None)
        session.setdefault("modification_areas", None)
        session.setdefault("modified_roadmap", None)
        session.setdefault("roadmap_modified_at", None)
        session.setdefault("transition_data", None)
        return session
    else:
        raise Exception("Session not found")

async def patch_session(session_id: str, updates: dict):
    response = supabase.from_("chat_sessions").update(updates).eq("id", session_id).execute()
    return response.data[0]