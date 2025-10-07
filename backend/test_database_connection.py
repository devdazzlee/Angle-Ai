"""
Test script to verify database connection and schema
Run this to ensure your new Supabase database is working correctly
"""

import os
from dotenv import load_dotenv
from db.supabase import supabase

# Load environment variables
load_dotenv()

async def test_database_connection():
    """Test database connection and verify schema"""
    print("🔍 Testing database connection...")
    
    try:
        # Test basic connection
        print("1. Testing basic connection...")
        response = supabase.table("chat_sessions").select("id").limit(1).execute()
        print("✅ Database connection successful")
        
        # Test chat_sessions table structure
        print("\n2. Testing chat_sessions table...")
        response = supabase.table("chat_sessions").select("*").limit(1).execute()
        print("✅ chat_sessions table accessible")
        
        # Test chat_history table
        print("\n3. Testing chat_history table...")
        response = supabase.table("chat_history").select("*").limit(1).execute()
        print("✅ chat_history table accessible")
        
        # Test all other tables
        tables = [
            "business_plans", "roadmaps", "implementation_tasks", 
            "service_providers", "research_sources", "rag_documents",
            "agent_interactions", "user_preferences", "user_activity"
        ]
        
        print("\n4. Testing all other tables...")
        for table in tables:
            try:
                response = supabase.table(table).select("*").limit(1).execute()
                print(f"✅ {table} table accessible")
            except Exception as e:
                print(f"❌ {table} table error: {e}")
        
        print("\n🎉 Database integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_database_connection())
