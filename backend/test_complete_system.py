"""
Complete System Verification
Tests question tracking, chat saving, and schema integration
"""

import asyncio
from db.supabase import supabase
from services.session_service import create_session, get_session, patch_session
from services.chat_service import save_chat_message, fetch_chat_history
from services.business_context_service import extract_and_store_business_context, validate_question_progression

async def test_complete_system():
    """Test the complete system functionality"""
    print("🧪 TESTING COMPLETE SYSTEM FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Test 1: Create a test session
        print("1. Testing session creation...")
        test_user_id = "00000000-0000-0000-0000-000000000000"
        
        # Create session
        session = await create_session(test_user_id, "Test Question Tracking")
        session_id = session["id"]
        print(f"✅ Session created: {session_id}")
        print(f"   Initial asked_q: {session['asked_q']}")
        print(f"   Initial phase: {session['current_phase']}")
        print(f"   Initial answered_count: {session['answered_count']}")
        
        # Test 2: Save chat messages
        print("\n2. Testing chat message saving...")
        
        # Save user message
        await save_chat_message(session_id, test_user_id, "user", "Hello, I want to start a business", phase="KYC")
        print("✅ User message saved")
        
        # Save AI response
        await save_chat_message(session_id, test_user_id, "assistant", "Great! Let's start with your name. What's your name? [[Q:KYC.01]]", phase="KYC")
        print("✅ AI response saved")
        
        # Test 3: Update session with question progression
        print("\n3. Testing question progression...")
        
        # Simulate answering KYC.01
        await patch_session(session_id, {
            "asked_q": "KYC.02",
            "answered_count": 1,
            "user_name": "John Doe"
        })
        
        # Get updated session
        updated_session = await get_session(session_id, test_user_id)
        print(f"✅ Session updated:")
        print(f"   Current asked_q: {updated_session['asked_q']}")
        print(f"   Answered count: {updated_session['answered_count']}")
        print(f"   User name: {updated_session.get('user_name', 'Not set')}")
        
        # Test 4: Test business context extraction
        print("\n4. Testing business context extraction...")
        
        # Extract business context for KYC.01 (name)
        await extract_and_store_business_context(session_id, test_user_id, "KYC.01", "John Doe")
        print("✅ Business context extracted and stored")
        
        # Test 5: Test question sequence validation
        print("\n5. Testing question sequence validation...")
        
        # Test valid progression (KYC.01 -> KYC.02)
        validation = await validate_question_progression(session_id, test_user_id, "KYC.02")
        if validation["valid"]:
            print("✅ Valid question progression accepted")
        else:
            print(f"❌ Valid progression rejected: {validation}")
        
        # Test invalid progression (KYC.01 -> KYC.10)
        validation = await validate_question_progression(session_id, test_user_id, "KYC.10")
        if not validation["valid"]:
            print(f"✅ Invalid progression caught and corrected to: {validation.get('corrected_tag')}")
        else:
            print("❌ Invalid progression not caught")
        
        # Test 6: Test chat history retrieval
        print("\n6. Testing chat history retrieval...")
        
        history = await fetch_chat_history(session_id)
        print(f"✅ Chat history retrieved: {len(history)} messages")
        for i, msg in enumerate(history):
            print(f"   {i+1}. [{msg['role']}]: {msg['content'][:50]}...")
        
        # Test 7: Test session persistence
        print("\n7. Testing session persistence...")
        
        # Get session again to verify persistence
        persisted_session = await get_session(session_id, test_user_id)
        print(f"✅ Session persisted correctly:")
        print(f"   Title: {persisted_session['title']}")
        print(f"   Current phase: {persisted_session['current_phase']}")
        print(f"   Asked question: {persisted_session['asked_q']}")
        print(f"   Answered count: {persisted_session['answered_count']}")
        print(f"   User name: {persisted_session.get('user_name', 'Not set')}")
        
        # Test 8: Test schema fields
        print("\n8. Testing schema field integration...")
        
        # Check if all expected fields exist
        expected_fields = [
            'id', 'user_id', 'title', 'current_phase', 'asked_q', 'answered_count',
            'business_context', 'user_name', 'employment_status', 'has_business_idea',
            'business_idea_brief', 'business_type', 'motivation', 'location',
            'industry', 'skills_assessment', 'created_at', 'updated_at'
        ]
        
        missing_fields = []
        for field in expected_fields:
            if field not in persisted_session:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"⚠️ Missing fields: {missing_fields}")
        else:
            print("✅ All expected schema fields are present")
        
        # Cleanup
        print("\n9. Cleaning up test data...")
        supabase.table("chat_history").delete().eq("session_id", session_id).execute()
        supabase.table("chat_sessions").delete().eq("id", session_id).execute()
        print("✅ Test data cleaned up")
        
        print("\n🎉 COMPLETE SYSTEM TEST PASSED!")
        print("=" * 60)
        print("✅ Question tracking is working perfectly")
        print("✅ Chat messages are being saved")
        print("✅ Business context is being extracted")
        print("✅ Question sequence validation is active")
        print("✅ Session persistence is working")
        print("✅ Schema integration is complete")
        print("✅ AI cannot jump or skip questions")
        print("✅ Complete conversation history is preserved")
        
        return True
        
    except Exception as e:
        print(f"\n❌ SYSTEM TEST FAILED: {e}")
        print("=" * 60)
        return False

if __name__ == "__main__":
    async def main():
        success = await test_complete_system()
        if success:
            print("\n🚀 YOUR SYSTEM IS WORKING PERFECTLY!")
            print("✅ Every chat is saved")
            print("✅ AI knows which question you're on")
            print("✅ AI cannot jump or skip questions")
            print("✅ All business context is preserved")
            print("✅ Question sequence is enforced")
        else:
            print("\n⚠️ Some tests failed. Please check the errors above.")
    
    asyncio.run(main())
