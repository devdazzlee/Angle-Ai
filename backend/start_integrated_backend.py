"""
Integrated Backend Startup Script
Starts the backend with complete database integration
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with these variables.")
        return False
    
    print("✅ All required environment variables are set")
    return True

async def test_database_connection():
    """Test database connection before starting server"""
    try:
        from db.supabase import supabase
        response = supabase.table("chat_sessions").select("id").limit(1).execute()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def start_backend():
    """Start the FastAPI backend server"""
    try:
        import uvicorn
        from main import app
        
        print("🚀 Starting integrated backend server...")
        print("📍 Server will be available at: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔄 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError:
        print("❌ Required dependencies not found. Please install requirements:")
        print("   pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")

async def main():
    """Main startup function"""
    print("🎯 ANGLE-AI BACKEND INTEGRATION STARTUP")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        return
    
    # Test database connection
    print("\n🔍 Testing database connection...")
    if not await test_database_connection():
        print("\n❌ Database connection failed. Please check your Supabase configuration.")
        return
    
    print("\n✅ All checks passed!")
    print("🚀 Starting integrated backend...")
    
    # Start the backend
    start_backend()

if __name__ == "__main__":
    asyncio.run(main())
