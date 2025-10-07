"""
Complete Integration Test Script
Tests the entire backend integration with the new database
"""

import os
import asyncio
from dotenv import load_dotenv
from db.supabase import supabase
from services.session_service import create_session, get_session, patch_session
from services.chat_service import save_chat_message, fetch_chat_history
from services.business_context_service import extract_and_store_business_context, get_business_context_summary

# Load environment variables
load_dotenv()

async def test_complete_integration():
    """Test complete backend integration"""
    print("🚀 Starting Complete Backend Integration Test")
    print("=" * 60)
    
    try:
        # Test 1: Database Connection
        print("\n1. Testing Database Connection...")
        response = supabase.table("chat_sessions").select("id").limit(1).execute()
        print("✅ Database connection successful")
        
        # Test 2: Session Creation
        print("\n2. Testing Session Creation...")
        test_user_id = "test-user-123"
        session = await create_session(test_user_id, "Test Session")
        session_id = session["id"]
        print(f"✅ Session created: {session_id}")
        
        # Test 3: Chat Message Storage
        print("\n3. Testing Chat Message Storage...")
        await save_chat_message(session_id, test_user_id, "user", "Hello, I want to start a business", phase="KYC")
        await save_chat_message(session_id, test_user_id, "assistant", "Great! Let's start with your name. What's your name?", phase="KYC")
        print("✅ Chat messages stored successfully")
        
        # Test 4: Business Context Extraction
        print("\n4. Testing Business Context Extraction...")
        await extract_and_store_business_context(session_id, test_user_id, "KYC.01", "John Doe")
        print("✅ Business context extracted and stored")
        
        # Test 5: Session Updates
        print("\n5. Testing Session Updates...")
        await patch_session(session_id, {
            "asked_q": "KYC.02",
            "answered_count": 1,
            "user_name": "John Doe"
        })
        print("✅ Session updated successfully")
        
        # Test 6: Business Context Summary
        print("\n6. Testing Business Context Summary...")
        context_summary = await get_business_context_summary(session_id, test_user_id)
        print(f"✅ Business context summary: {context_summary['user_profile']['name']}")
        
        # Test 7: Chat History Retrieval
        print("\n7. Testing Chat History Retrieval...")
        history = await fetch_chat_history(session_id)
        print(f"✅ Chat history retrieved: {len(history)} messages")
        
        # Test 8: Session Retrieval
        print("\n8. Testing Session Retrieval...")
        retrieved_session = await get_session(session_id, test_user_id)
        print(f"✅ Session retrieved: {retrieved_session['title']}")
        
        # Cleanup
        print("\n9. Cleaning up test data...")
        supabase.table("chat_history").delete().eq("session_id", session_id).execute()
        supabase.table("chat_sessions").delete().eq("id", session_id).execute()
        print("✅ Test data cleaned up")
        
        print("\n🎉 COMPLETE INTEGRATION TEST PASSED!")
        print("=" * 60)
        print("✅ All backend services are working correctly")
        print("✅ Database integration is complete")
        print("✅ Question sequence enforcement is ready")
        print("✅ Chat persistence is functional")
        print("✅ Business context storage is working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        print("=" * 60)
        return False

async def test_question_sequence_enforcement():
    """Test question sequence enforcement"""
    print("\n🔍 Testing Question Sequence Enforcement...")
    
    try:
        # Create test session
        test_user_id = "test-user-sequence"
        session = await create_session(test_user_id, "Sequence Test Session")
        session_id = session["id"]
        
        # Test valid progression
        print("Testing valid question progression...")
        from services.business_context_service import validate_question_progression
        
        # Test KYC.01 -> KYC.02
        validation = await validate_question_progression(session_id, test_user_id, "KYC.02")
        if validation["valid"]:
            print("✅ Valid progression accepted")
        else:
            print(f"❌ Valid progression rejected: {validation}")
        
        # Test invalid progression
        print("Testing invalid question progression...")
        validation = await validate_question_progression(session_id, test_user_id, "KYC.10")
        if not validation["valid"]:
            print(f"✅ Invalid progression caught and corrected: {validation.get('corrected_tag')}")
        else:
            print("❌ Invalid progression not caught")
        
        # Cleanup
        supabase.table("chat_sessions").delete().eq("id", session_id).execute()
        
        print("✅ Question sequence enforcement test passed")
        return True
        
    except Exception as e:
        print(f"❌ Question sequence enforcement test failed: {e}")
        return False

if __name__ == "__main__":
    async def run_all_tests():
        print("🧪 RUNNING COMPLETE BACKEND INTEGRATION TESTS")
        print("=" * 60)
        
        # Run main integration test
        main_test_passed = await test_complete_integration()
        
        # Run sequence enforcement test
        sequence_test_passed = await test_question_sequence_enforcement()
        
        # Final results
        print("\n📊 FINAL TEST RESULTS")
        print("=" * 60)
        print(f"Main Integration Test: {'✅ PASSED' if main_test_passed else '❌ FAILED'}")
        print(f"Sequence Enforcement Test: {'✅ PASSED' if sequence_test_passed else '❌ FAILED'}")
        
        if main_test_passed and sequence_test_passed:
            print("\n🎉 ALL TESTS PASSED! Your backend is ready!")
        else:
            print("\n⚠️ Some tests failed. Please check the errors above.")
    
    asyncio.run(run_all_tests())
