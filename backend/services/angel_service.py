from openai import AsyncOpenAI
import os
import json
import re
from datetime import datetime
from utils.constant import ANGEL_SYSTEM_PROMPT

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Web search throttling
web_search_count = 0
web_search_reset_time = datetime.now()

def should_conduct_web_search():
    """Throttle web searches to prevent excessive API calls"""
    global web_search_count, web_search_reset_time
    
    # Reset counter every 10 seconds for faster reset during implementation
    if (datetime.now() - web_search_reset_time).seconds > 10:
        web_search_count = 0
        web_search_reset_time = datetime.now()
    
    # Allow maximum 2 web searches per 10 seconds for better performance
    if web_search_count >= 2:
        return False
    
    web_search_count += 1
    return True

TAG_PROMPT = """CRITICAL: You MUST include a machine-readable tag in EVERY response that contains a question. Use this exact format:
[[Q:<PHASE>.<NN>]] 

Examples:
- [[Q:KYC.01]] What's your name?
- [[Q:KYC.02]] What is your preferred communication style?
- [[Q:BUSINESS_PLAN.01]] What is your business idea?
- [[Q:BUSINESS_PLAN.19]] What is your revenue model?
- [[Q:BUSINESS_PLAN.20]] How will you market your business?

IMPORTANT RULES:
1. The tag must be at the beginning of your question, before any other text
2. Question numbers must be sequential and correct for the current phase
3. For BUSINESS_PLAN phase, questions should be numbered 01 through 46
4. NEVER jump backwards in question numbers (e.g., from 19 to 10)
5. If you're continuing a conversation, increment the question number appropriately

FAILURE TO INCLUDE CORRECT TAGS WILL BREAK THE SYSTEM. ALWAYS include the correct sequential tag before asking any question.

FORMATTING REQUIREMENT: Always use structured format for questions - NEVER paragraph format!"""

WEB_SEARCH_PROMPT = """You have access to web search capabilities, but use them VERY SPARINGLY during Implementation phase.

IMPLEMENTATION PHASE RULES:
• Use web search VERY SPARINGLY - maximum 1 search per response
• Focus on delivering quick, practical implementation steps
• Users expect fast responses during implementation (3-5 seconds max)
• Only search for the most critical information gaps
• AVOID multiple web searches - they cause delays

WEB SEARCH GUIDELINES:
• When web search results are provided, you MUST include them in your response immediately
• Use previous calendar year for search queries (e.g., "2024" instead of "2023")
• Provide comprehensive answers based on the research findings
• Do not ask the user to wait or send another message - deliver results immediately
• Include specific details from the research in your response
• Do not just say "I'm conducting research" - provide the actual research results

To use web search, include in your response: WEBSEARCH_QUERY: [your search query]"""

async def conduct_web_search(query):
    """Conduct web search using OpenAI's web search tool with progress indication"""
    try:
        # Check if we should conduct web search (throttling)
        if not should_conduct_web_search():
            print(f"🚫 Web search throttled - returning immediately. Query: {query[:50]}...")
            return "I'll provide guidance based on my existing knowledge to ensure fast response."
        
        print(f"🔍 Conducting web search: {query}")
        
        # Limit query length to prevent excessive API calls
        if len(query) > 80:  # Further reduced to 80 characters for faster processing
            query = query[:80] + "..."
        
        # Use a faster, more efficient approach with shorter timeout
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Use faster model for web search
            messages=[{
                "role": "user", 
                "content": f"Search for current information about: {query}. Provide a concise summary of key findings in 1 sentence."
            }],
            temperature=0.1,  # Lower temperature for more focused results
            max_tokens=50,  # Further reduced token limit for faster processing
            timeout=3.0  # 3 second timeout for faster response
        )
        
        # Extract search results from response
        search_results = response.choices[0].message.content
        print(f"✅ Web search completed for: {query[:50]}...")
        return search_results
    
    except Exception as e:
        print(f"❌ Web search error: {e}")
        return "I'll provide guidance based on my existing knowledge."

def trim_conversation_history(history, max_messages=10):
    """Trim conversation history to prevent context from growing too large"""
    if len(history) <= max_messages:
        return history
    
    # Keep the most recent messages
    return history[-max_messages:]

def format_response_structure(reply):
    """Format AI responses to use proper structured format instead of paragraph form"""
    
    formatted_reply = reply
    
    # Check if this should be a dropdown question (Yes/No or multiple choice)
    is_yes_no_question = ("yes" in formatted_reply.lower() and "no" in formatted_reply.lower() and 
                         any(phrase in formatted_reply.lower() for phrase in ["have you", "do you", "are you", "would you"]))
    
    is_work_situation_question = "work situation" in formatted_reply.lower()
    
    is_multiple_choice_question = ("•" in formatted_reply or "○" in formatted_reply or 
                                  any(option in formatted_reply.lower() for option in ["full-time employed", "part-time", "student", "unemployed"]))
    
    # For dropdown questions, remove the options from the message
    if is_yes_no_question:
        # Remove Yes/No options
        formatted_reply = re.sub(r'\n\n• Yes\n• No', '', formatted_reply)
        formatted_reply = re.sub(r'\n• Yes\n• No', '', formatted_reply)
        formatted_reply = re.sub(r'\n\nYes / No', '', formatted_reply)
        formatted_reply = re.sub(r'\nYes / No', '', formatted_reply)
    
    elif is_work_situation_question:
        # Remove work situation options
        work_options_pattern = r'\n\n• Full-time employed\n• Part-time\n• Student\n• Unemployed\n• Self-employed/freelancer\n• Other'
        formatted_reply = re.sub(work_options_pattern, '', formatted_reply)
        
        # Also handle single-line format
        work_options_single_pattern = r'\n• Full-time employed\n• Part-time\n• Student\n• Unemployed\n• Self-employed/freelancer\n• Other'
        formatted_reply = re.sub(work_options_single_pattern, '', formatted_reply)
    
    elif is_multiple_choice_question and not is_yes_no_question:
        # Remove bullet point options for other multiple choice questions
        # Pattern: "Question?\n\n• Option1\n• Option2\n• Option3"
        multi_choice_pattern = r'([^?]+\?)\s*\n\n(• [^\n]+(?:\n• [^\n]+)*)'
        formatted_reply = re.sub(multi_choice_pattern, r'\1', formatted_reply)
        
        # Also handle single-line format
        multi_choice_single_pattern = r'([^?]+\?)\s*\n(• [^\n]+(?:\n• [^\n]+)*)'
        formatted_reply = re.sub(multi_choice_single_pattern, r'\1', formatted_reply)
        
        # Handle circle bullets (○) - remove these options too
        circle_choice_pattern = r'([^?]+\?)\s*\n\n(○ [^\n]+(?:\n○ [^\n]+)*)'
        formatted_reply = re.sub(circle_choice_pattern, r'\1', formatted_reply)
        
        # Also handle single-line format for circles
        circle_choice_single_pattern = r'([^?]+\?)\s*\n(○ [^\n]+(?:\n○ [^\n]+)*)'
        formatted_reply = re.sub(circle_choice_single_pattern, r'\1', formatted_reply)
    
    # Specific formatting for work situation question (if not already handled)
    if "work situation" in formatted_reply.lower() and "?" in formatted_reply and not is_work_situation_question:
        # Pattern: "What's your current work situation? Full-time employed Part-time Student Unemployed Self-employed/freelancer Other"
        work_pattern = r'([^?]+\?)\s+(Full-time employed\s+Part-time\s+Student\s+Unemployed\s+Self-employed/freelancer\s+Other)'
        formatted_reply = re.sub(work_pattern, 
            r'\1\n\n• Full-time employed\n• Part-time\n• Student\n• Unemployed\n• Self-employed/freelancer\n• Other', 
            formatted_reply)
    
    # Specific formatting for business before question
    if "business before" in formatted_reply.lower() and "?" in formatted_reply:
        # Pattern: "Have you started a business before? Yes / No"
        business_pattern = r'([^?]+\?)\s+(Yes\s*/\s*No)'
        formatted_reply = re.sub(business_pattern, r'\1\n\n• Yes\n• No', formatted_reply)
    
    # General pattern for Yes/No questions (if not already handled)
    if not is_yes_no_question:
        # Pattern: "Question? Yes / No" or "Question? Yes/No"
        yes_no_pattern = r'([^?]+\?)\s+(Yes\s*/\s*No)'
        formatted_reply = re.sub(yes_no_pattern, r'\1\n\n• Yes\n• No', formatted_reply)
    
    # General pattern for multiple choice questions (if not already handled)
    if not is_multiple_choice_question:
        # Pattern: "Question? Option1 Option2 Option3 Option4"
        multi_choice_pattern = r'([^?]+\?)\s+([A-Za-z\s]+(?:employed|time|Student|Unemployed|freelancer|Other)[^?]*)'
        formatted_reply = re.sub(multi_choice_pattern, 
            lambda m: f"{m.group(1)}\n\n• {m.group(2).replace(' ', ' • ')}", 
            formatted_reply)
    
    # Convert circle bullets to regular bullets for consistency
    formatted_reply = re.sub(r'○\s*', '• ', formatted_reply)
    
    # Clean up any double bullet points
    formatted_reply = re.sub(r'•\s*•\s*', '• ', formatted_reply)
    
    # Ensure proper spacing
    formatted_reply = re.sub(r'\n{3,}', '\n\n', formatted_reply)
    
    return formatted_reply

def ensure_question_separation(reply, session_data=None):
    """Ensure questions are properly separated and not combined"""
    
    # Check if this is a business plan question that might be combined
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Look for patterns where multiple questions are combined
        combined_patterns = [
            # Pattern: "Question1? Question2?"
            (r'([^?]+\?)\s+([A-Z][^?]+\?)', r'\1\n\n\2'),
            # Pattern: "Question1. Question2?"
            (r'([^?]+\.)\s+([A-Z][^?]+\?)', r'\1\n\n\2'),
        ]
        
        for pattern, replacement in combined_patterns:
            reply = re.sub(pattern, replacement, reply)
    
    return reply

def validate_business_plan_sequence(reply, session_data=None):
    """Ensure business plan questions follow proper sequence"""
    
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Extract current question number from tag
        tag_match = re.search(r'\[\[Q:BUSINESS_PLAN\.(\d+)\]\]', reply)
        if tag_match:
            current_q_num = int(tag_match.group(1))
            asked_q = session_data.get("asked_q", "BUSINESS_PLAN.01")
            
            # Check if we're jumping ahead
            if "BUSINESS_PLAN." in asked_q:
                last_q_num = int(asked_q.split(".")[1])
                if current_q_num > last_q_num + 1:
                    print(f"⚠️ WARNING: Jumping from question {last_q_num} to {current_q_num}")
                    # Force back to next sequential question
                    next_q = f"BUSINESS_PLAN.{last_q_num + 1:02d}"
                    reply = re.sub(r'\[\[Q:BUSINESS_PLAN\.\d+\]\]', f'[[Q:{next_q}]]', reply)
                    print(f"🔧 Corrected to: {next_q}")
    
    return reply

def fix_verification_flow(reply, session_data=None):
    """Fix verification flow to separate verification from next question"""
    
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Look for patterns where verification is combined with next question
        verification_patterns = [
            # Pattern: "Here's what I've captured... Does this look accurate? [Next question]"
            (r'(Here\'s what I\'ve captured so far:.*?Does this look accurate to you\?)\s+([A-Z][^?]+\?)', 
             r'\1\n\nPlease respond with "Accept" or "Modify" to continue.'),
            
            # Pattern: "Feel free to refine... What specific products..."
            (r'(Feel free to refine or expand on this as we continue\.)\s+([A-Z][^?]+\?)', 
             r'Does this information look accurate to you? If not, please let me know where you\'d like to modify and we\'ll work through this some more.\n\nPlease respond with "Accept" or "Modify" to continue.'),
        ]
        
        for pattern, replacement in verification_patterns:
            reply = re.sub(pattern, replacement, reply, flags=re.DOTALL)
        
        # Check if this is a verification message that should trigger Accept/Modify buttons
        verification_keywords = [
            "does this look accurate",
            "does this look correct", 
            "is this accurate",
            "is this correct",
            "please let me know where you'd like to modify"
        ]
        
        if any(keyword in reply.lower() for keyword in verification_keywords):
            # Ensure it ends with proper instruction
            if "Please respond with \"Accept\" or \"Modify\"" not in reply:
                reply += "\n\nPlease respond with \"Accept\" or \"Modify\" to continue."
    
    return reply

def prevent_ai_molding(reply, session_data=None):
    """Prevent AI from molding user answers into mission, vision, USP without verification"""
    
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Look for patterns where AI molds answers without verification
        molding_patterns = [
            # Pattern: AI creates mission, vision, USP from user input without asking
            (r'(Based on your input, here\'s what I\'ve created for you:.*?Mission:.*?Vision:.*?Unique Selling Proposition:.*?)([A-Z][^?]+\?)', 
             r'Here\'s what I\'ve captured so far: [summary]. Does this look accurate to you? If not, please let me know where you\'d like to modify and we\'ll work through this some more.\n\nPlease respond with "Accept" or "Modify" to continue.'),
            
            # Pattern: AI summarizes and immediately asks next question
            (r'(Great! Based on your answers, here\'s what I understand:.*?)([A-Z][^?]+\?)', 
             r'Here\'s what I\'ve captured so far: [summary]. Does this look accurate to you? If not, please let me know where you\'d like to modify and we\'ll work through this some more.\n\nPlease respond with "Accept" or "Modify" to continue.'),
        ]
        
        for pattern, replacement in molding_patterns:
            reply = re.sub(pattern, replacement, reply, flags=re.DOTALL)
        
        # Check if AI is molding without verification
        molding_keywords = [
            "based on your input, here's what i've created",
            "here's what i understand about your business",
            "let me create a mission statement for you",
            "based on your answers, here's your mission"
        ]
        
        if any(keyword in reply.lower() for keyword in molding_keywords):
            # Replace with proper verification request
            reply = "Here's what I've captured so far: [summary]. Does this look accurate to you? If not, please let me know where you'd like to modify and we'll work through this some more.\n\nPlease respond with \"Accept\" or \"Modify\" to continue."
    
    return reply

def suggest_draft_if_relevant(reply, session_data, user_input, history):
    """Suggest using Draft if user has already provided relevant information"""
    
    if not history or not user_input:
        return reply
    
    # Don't suggest draft in KYC phase
    if session_data and session_data.get("current_phase") == "KYC":
        return reply
    
    # Keywords that indicate the user might have already provided relevant information
    relevant_keywords = {
        'target audience': ['audience', 'customers', 'demographic', 'market', 'millennials', 'gen z', 'generation'],
        'business name': ['name', 'brand', 'company', 'business'],
        'products/services': ['product', 'service', 'offer', 'sell', 'provide'],
        'mission/vision': ['mission', 'vision', 'purpose', 'goal', 'objective'],
        'location': ['location', 'city', 'country', 'area', 'region'],
        'industry': ['industry', 'sector', 'field', 'business type'],
        'resources': ['resources', 'tools', 'equipment', 'staff', 'team', 'budget']
    }
    
    # Check if current question matches any of these categories
    current_question = reply.lower()
    relevant_category = None
    
    for category, keywords in relevant_keywords.items():
        if any(keyword in current_question for keyword in keywords):
            relevant_category = category
            break
    
    if relevant_category:
        # Check if user has provided information in this category before
        user_has_relevant_info = False
        
        # Check conversation history for relevant information
        for msg in history:
            if msg.get('role') == 'user' and len(msg.get('content', '')) > 10:
                user_content = msg['content'].lower()
                if any(keyword in user_content for keyword in relevant_keywords[relevant_category]):
                    user_has_relevant_info = True
                    break
        
        # Check for various tip patterns that might already exist
        tip_patterns = [
            "💡 Quick Tip:",
            "💡 **Quick Tip**:",
            "💡 **Pro Tip**:",
            "💡 Quick tip:",
            "💡 **Quick tip**:",
            "💡 **Pro tip**:",
            "Quick Tip:",
            "**Quick Tip**:",
            "**Pro Tip**:",
            "Quick tip:",
            "**Quick tip**:",
            "**Pro tip**:"
        ]
        
        has_existing_tip = any(pattern in reply for pattern in tip_patterns)
        
        if user_has_relevant_info and not has_existing_tip:
            # Add suggestion to use Draft
            draft_suggestion = f"\n\n💡 **Quick Tip**: Based on some info you've previously entered, you can also select **\"Draft\"** and I'll use that information to create a draft answer for you to review and save you some time."
            reply += draft_suggestion
    
    return reply

def check_for_section_summary(current_tag, session_data, history):
    """Check if we need to provide a section summary based on the current question tag"""
    
    if not current_tag or not current_tag.startswith("BUSINESS_PLAN."):
        return None
    
    try:
        question_num = int(current_tag.split(".")[1])
    except (ValueError, IndexError):
        return None
    
    # Define section boundaries and their summary requirements
    section_boundaries = {
        4: "SECTION 1 SUMMARY REQUIRED: After BUSINESS_PLAN.04, provide:",
        8: "SECTION 2 SUMMARY REQUIRED: After BUSINESS_PLAN.08, provide:",
        12: "SECTION 3 SUMMARY REQUIRED: After BUSINESS_PLAN.12, provide:",
        17: "SECTION 4 SUMMARY REQUIRED: After BUSINESS_PLAN.17, provide:",
        25: "SECTION 5 SUMMARY REQUIRED: After BUSINESS_PLAN.25, provide:",
        31: "SECTION 6 SUMMARY REQUIRED: After BUSINESS_PLAN.31, provide:",
        38: "SECTION 7 SUMMARY REQUIRED: After BUSINESS_PLAN.38, provide:",
        42: "SECTION 8 SUMMARY REQUIRED: After BUSINESS_PLAN.42, provide:",
        46: "SECTION 9 SUMMARY REQUIRED: After BUSINESS_PLAN.46, provide:"
    }
    
    # Check if we're at a section boundary
    if question_num in section_boundaries:
        return {
            "trigger_question": question_num,
            "summary_type": section_boundaries[question_num],
            "section_name": get_section_name(question_num)
        }
    
    return None

def get_section_name(question_num):
    """Get the section name based on question number"""
    section_names = {
        4: "Business Foundation",
        8: "Product/Service Details", 
        12: "Market Research",
        17: "Location & Operations",
        25: "Financial Planning",
        31: "Marketing & Sales",
        38: "Legal & Compliance",
        42: "Growth & Scaling",
        46: "Risk Management"
    }
    return section_names.get(question_num, "Unknown Section")

def add_critiquing_insights(reply, session_data=None, user_input=None):
    """Add critiquing insights and coaching based on user's business field (50/50 approach)"""
    
    if not user_input or not session_data:
        return reply
    
    # Extract business-related keywords from user input
    business_keywords = {
        "social media": ["social media", "instagram", "tiktok", "youtube", "influencer", "content creator", "wine critic", "short-form videos"],
        "food": ["restaurant", "food", "cooking", "chef", "culinary", "dining", "wine", "beverage"],
        "technology": ["app", "software", "tech", "digital", "online", "platform", "website", "mobile"],
        "retail": ["store", "shop", "retail", "product", "selling", "ecommerce", "marketplace"],
        "services": ["service", "consulting", "coaching", "training", "professional", "review", "critique"],
        "health": ["health", "fitness", "wellness", "medical", "therapy", "nutrition"],
        "education": ["education", "teaching", "learning", "course", "training", "tutorial"],
        "entertainment": ["entertainment", "music", "art", "creative", "media", "video", "content"]
    }
    
    # Identify the business field
    user_input_lower = user_input.lower()
    identified_field = None
    
    for field, keywords in business_keywords.items():
        if any(keyword in user_input_lower for keyword in keywords):
            identified_field = field
            break
    
    # Add critiquing insights based on the field (50/50 approach)
    if identified_field:
        critiquing_insights = {
            "social media": "Social media influencing is a very popular field with significant opportunities. Some of the most successful influencers cross-post to different platforms like YouTube, Threads, and LinkedIn to ensure reach and expand their audiences. Podcasts are also an interesting medium that has gained significant popularity in recent years. Consider building a consistent brand voice across all platforms.",
            "food": "The food and beverage industry is highly competitive but rewarding for those who find their niche. Successful food businesses often focus on unique flavors, local sourcing, and creating memorable experiences. Wine criticism, in particular, has seen growth with the rise of social media sommeliers. Consider the importance of food safety certifications and local health department requirements.",
            "technology": "The tech industry moves quickly, so staying updated with trends is crucial for success. Consider the importance of user experience design, scalability, and data security. Many successful tech startups begin with a minimum viable product (MVP) approach to test market demand before full development.",
            "retail": "Retail success often depends on understanding your target market and creating a strong brand identity. Consider both online and offline presence, inventory management, and customer service excellence. The key is finding the right balance between quality and accessibility.",
            "services": "Service-based businesses rely heavily on reputation and word-of-mouth marketing. Consider the importance of building strong client relationships, maintaining consistent quality, and having clear service agreements. Reviews and testimonials are particularly valuable in this space.",
            "health": "Health-related businesses require careful attention to regulations and certifications. Consider the importance of building trust with clients, maintaining confidentiality, and staying current with industry standards. Credibility and expertise are essential in this field.",
            "education": "Education businesses thrive on creating engaging learning experiences. Consider the importance of curriculum design, student engagement, and measuring learning outcomes. The best educational content combines practical knowledge with interactive elements.",
            "entertainment": "Entertainment businesses often succeed through unique content and strong audience engagement. Consider the importance of building a loyal following and creating content that resonates with your target audience. Consistency and authenticity are key to long-term success."
        }
        
        insight = critiquing_insights.get(identified_field)
        if insight:
            # Insert the insight after the acknowledgment but before the question
            lines = reply.split('\n')
            for i, line in enumerate(lines):
                if '?' in line and len(line.strip()) > 10:
                    # Insert insight before the question
                    lines.insert(i, f"\n{insight}\n")
                    break
            
            reply = '\n'.join(lines)
    
    return reply

def identify_support_areas(session_data, history):
    """Proactively identify areas where the entrepreneur needs the most support based on KYC and business plan answers"""
    
    if not session_data or not history:
        return None
    
    # Analyze conversation history for gaps and areas needing support
    support_areas = []
    
    # Check for common areas that need support
    conversation_text = " ".join([msg.get('content', '') for msg in history if msg.get('role') == 'user'])
    conversation_lower = conversation_text.lower()
    
    # Financial planning support
    if any(keyword in conversation_lower for keyword in ['budget', 'funding', 'money', 'cost', 'price', 'financial']):
        if not any(keyword in conversation_lower for keyword in ['detailed financial', 'financial projections', 'break even', 'revenue model']):
            support_areas.append("Financial Planning & Projections")
    
    # Market research support
    if any(keyword in conversation_lower for keyword in ['market', 'customers', 'competition', 'target']):
        if not any(keyword in conversation_lower for keyword in ['market research', 'competitive analysis', 'customer demographics', 'market size']):
            support_areas.append("Market Research & Competitive Analysis")
    
    # Operations support
    if any(keyword in conversation_lower for keyword in ['business', 'operations', 'process', 'staff']):
        if not any(keyword in conversation_lower for keyword in ['operational plan', 'staffing plan', 'processes', 'systems']):
            support_areas.append("Operations & Process Planning")
    
    # Legal/compliance support
    if any(keyword in conversation_lower for keyword in ['legal', 'license', 'permit', 'regulation', 'compliance']):
        if not any(keyword in conversation_lower for keyword in ['business structure', 'licenses required', 'legal requirements']):
            support_areas.append("Legal Structure & Compliance")
    
    # Marketing support
    if any(keyword in conversation_lower for keyword in ['marketing', 'sales', 'customers', 'brand']):
        if not any(keyword in conversation_lower for keyword in ['marketing strategy', 'sales process', 'brand positioning', 'customer acquisition']):
            support_areas.append("Marketing & Sales Strategy")
    
    # Technology support
    if any(keyword in conversation_lower for keyword in ['technology', 'software', 'website', 'digital', 'online']):
        if not any(keyword in conversation_lower for keyword in ['technology requirements', 'digital tools', 'software needs']):
            support_areas.append("Technology & Digital Tools")
    
    return support_areas

def add_proactive_support_guidance(reply, session_data, history):
    """Add proactive support guidance based on identified areas needing help"""
    
    # Don't add support guidance in KYC phase
    if session_data and session_data.get("current_phase") == "KYC":
        return reply
    
    # Only add support guidance if not already present in the reply
    tip_patterns = [
        "💡 Quick Tip:",
        "💡 **Quick Tip**:",
        "💡 **Pro Tip**:",
        "💡 Quick tip:",
        "💡 **Quick tip**:",
        "💡 **Pro tip**:",
        "Quick Tip:",
        "**Quick Tip**:",
        "**Pro Tip**:",
        "Quick tip:",
        "**Quick tip**:",
        "**Pro tip**:",
        "🎯 Areas Where You May Need Additional Support:"
    ]
    
    has_existing_guidance = any(pattern in reply for pattern in tip_patterns)
    
    if has_existing_guidance:
        return reply
    
    support_areas = identify_support_areas(session_data, history)
    
    if support_areas and len(support_areas) > 0:
        support_guidance = "\n\n**🎯 Areas Where You May Need Additional Support:**\n"
        support_guidance += "Based on your responses, I've identified these areas where you might benefit from deeper guidance:\n\n"
        
        for area in support_areas:
            support_guidance += f"• **{area}** - Consider using 'Support' for detailed guidance in this area\n"
        
        support_guidance += "\n💡 **Pro Tip:** Use 'Support' followed by any of these areas for comprehensive guidance and strategic questions to help you think through these topics more thoroughly."
        
        reply += support_guidance
    
    return reply

def ensure_proper_question_formatting(reply, session_data=None):
    """Ensure questions are properly formatted with line breaks and structure"""
    
    # Look for patterns where questions are not properly formatted
    formatting_patterns = [
        # Pattern: Yes/No questions without proper formatting
        (r'([^?]+\?)\s+(Yes\s*/\s*No)', r'\1\n\n• Yes\n• No'),
        # Pattern: Question without proper line breaks
        (r'([^?]+\?)\s+([A-Z][^?]+)', r'\1\n\n\2'),
        # Pattern: Multiple choice options without proper formatting
        (r'([^?]+\?)\s+([A-Z][^?]+(?:employed|time|Student|Unemployed|freelancer|Other)[^?]*)', 
         r'\1\n\n• \2'),
    ]
    
    for pattern, replacement in formatting_patterns:
        reply = re.sub(pattern, replacement, reply)
    
    # Ensure proper spacing between sections
    reply = re.sub(r'\n{3,}', '\n\n', reply)
    
    return reply

def inject_missing_tag(reply, session_data=None):
    """Inject a tag if the AI forgot to include one"""
    # Check if reply already has a tag
    if "[[Q:" in reply:
        return reply
    
    # Check if this is a command response (Draft, Support, Scrapping) - don't inject tags for these
    command_indicators = [
        "Here's a draft based on what you've shared",
        "Let's work through this together",
        "Here's a refined version of your thoughts",
        "I'll create additional content for you",
        "Verification:",
        "Here's what I've captured so far:"
    ]
    
    if any(indicator in reply for indicator in command_indicators):
        # This is a command response, don't inject a tag - stay on current question
        return reply
    
    # Try to determine the current phase and question number
    current_phase = "KYC"  # Default
    question_num = "01"    # Default
    
    if session_data:
        current_phase = session_data.get("current_phase", "KYC")
        asked_q = session_data.get("asked_q", "KYC.01")
        if "." in asked_q:
            phase, num = asked_q.split(".")
            current_phase = phase
            # Use current question number, don't increment for command responses
            question_num = num
    
    # If this looks like a question (contains ?), inject a tag
    if "?" in reply and len(reply.strip()) > 10:
        tag = f"[[Q:{current_phase}.{question_num}]]"
        # Insert tag at the beginning of the first sentence that contains a question
        lines = reply.split('\n')
        for i, line in enumerate(lines):
            if '?' in line and len(line.strip()) > 10:
                # Clean up the line and add tag
                clean_line = line.strip()
                lines[i] = f"{tag} {clean_line}"
                break
        return '\n'.join(lines)
    
    return reply

async def handle_kyc_completion(session_data, history):
    """Handle the transition from KYC completion to Business Plan phase"""
    
    # Return the completion message and trigger transition
    acknowledgment = """That's fantastic! Your proactive approach will help ensure we make the most of our time together and that you get the guidance you need when you need it.

🎉 **Congratulations! You've completed your entrepreneurial profile!** 🎉

Here's what I've learned about you and your goals:

• You're ready to take a proactive approach to building your business
• You've shared valuable insights about your experience, goals, and preferences
• You're prepared to dive deep into the business planning process

Now we're moving into the exciting Business Planning phase! This is where we'll dive deep into every aspect of your business idea. I'll be asking detailed questions about your product, market, finances, and strategy.

During this phase, I'll be conducting research in the background to provide you with industry insights, competitive analysis, and market data to enrich your business plan. Don't worry - this happens automatically and securely.

As we go through each question, I'll provide both supportive encouragement and constructive coaching to help you think through each aspect thoroughly. Remember, this comprehensive approach ensures your final business plan is detailed and provides you with a strong starting point of information that will help you launch your business. The more detailed answers you provide, the better I can help support you to bring your business to life.

Let's build the business of your dreams together!

*'The way to get started is to quit talking and begin doing.' - Walt Disney*

Ready to dive into your business planning?"""
    
    return {
        "reply": acknowledgment,
        "transition_phase": "KYC_TO_BUSINESS_PLAN",
        "patch_session": {
            "current_phase": "BUSINESS_PLAN",
            "asked_q": "BUSINESS_PLAN.01",
            "answered_count": 0
        }
    }

async def handle_business_plan_completion(session_data, history):
    """Handle the transition from Business Plan completion to Roadmap phase"""
    
    # Generate comprehensive business plan summary
    business_plan_summary = await generate_business_plan_summary(session_data, history)
    
    # Create the transition message
    transition_message = f"""🎉 **CONGRATULATIONS! Planning Champion Award** 🎉

You've successfully completed your comprehensive business plan! This is a significant milestone in your entrepreneurial journey.

**"Success is not final; failure is not fatal: it is the courage to continue that counts."** – Winston Churchill

---

## 📋 **Comprehensive Business Plan Recap**

{business_plan_summary}

---

## 🎯 **What's Next: Roadmap Generation**

Based on your detailed business plan, I will now generate a comprehensive, actionable launch roadmap that translates your plan into explicit, chronological tasks. This roadmap will include:

• **Legal Formation** - Business structure, licensing, permits
• **Financial Planning** - Funding strategies, budgeting, accounting setup
• **Product & Operations** - Supply chain, equipment, operational processes
• **Marketing & Sales** - Brand positioning, customer acquisition, sales processes
• **Full Launch & Scaling** - Go-to-market strategy, growth planning

The roadmap will be tailored specifically to your business, industry, and location, with research-backed recommendations and local service provider options.

---

## 🚀 **Ready to Move Forward?**

Please review your business plan summary above. If everything looks accurate and complete, you can:

**✅ Approve Plan** - Proceed to roadmap generation
**🔄 Revisit Plan** - Modify any aspects that need adjustment

What would you like to do?"""

    return {
        "reply": transition_message,
        "web_search_status": {"is_searching": False, "query": None},
        "immediate_response": None,
        "transition_phase": "PLAN_TO_ROADMAP",
        "business_plan_summary": business_plan_summary
    }

async def generate_business_plan_summary(session_data, history):
    """Generate a comprehensive summary of the business plan"""
    
    # Extract key information from session data and history
    summary_sections = []
    
    # Business Foundation
    if session_data.get("business_idea_brief"):
        summary_sections.append(f"**Business Idea:** {session_data.get('business_idea_brief')}")
    
    if session_data.get("business_type"):
        summary_sections.append(f"**Business Type:** {session_data.get('business_type')}")
    
    if session_data.get("industry"):
        summary_sections.append(f"**Industry:** {session_data.get('industry')}")
    
    if session_data.get("location"):
        summary_sections.append(f"**Location:** {session_data.get('location')}")
    
    if session_data.get("motivation"):
        summary_sections.append(f"**Motivation:** {session_data.get('motivation')}")
    
    # Extract additional information from conversation history
    user_responses = [msg.get('content', '') for msg in history if msg.get('role') == 'user']
    conversation_text = ' '.join(user_responses)
    
    # Generate AI-powered summary
    summary_prompt = f"""
    Create a comprehensive business plan summary based on the following information:
    
    Session Data: {session_data}
    Conversation History: {conversation_text[:2000]}  # Limit to avoid token limits
    
    Provide a structured summary that includes:
    1. Business Overview
    2. Target Market
    3. Products/Services
    4. Business Model
    5. Key Strategies
    6. Financial Considerations
    7. Next Steps
    
    Make it professional and comprehensive, highlighting the key decisions and milestones achieved.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.6,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating business plan summary: {e}")
        return "Business plan summary generation in progress..."

def provide_critiquing_feedback(user_msg, session_data, history):
    """
    Provide constructive critique and challenging feedback to push for deeper thinking
    """
    # Don't critique simple yes/no answers or very short responses to simple questions
    if not user_msg or len(user_msg.strip()) < 5:
        return None
    
    # Check for vague or unrealistic answers only for complex questions
    vague_indicators = ["maybe", "probably", "i think", "not sure", "don't know", "maybe", "possibly"]
    if any(indicator in user_msg.lower() for indicator in vague_indicators) and len(user_msg.strip()) > 50:
        return {
            "reply": f"I notice some uncertainty in your response. Let me challenge you to think deeper: What specific research have you done to support this? What are the concrete steps you're considering? What potential obstacles do you foresee, and how would you address them?",
            "web_search_status": {"is_searching": False, "query": None, "completed": False}
        }
    
    # Check for unrealistic assumptions
    unrealistic_indicators = ["easy", "simple", "quick", "fast", "guaranteed", "definitely will work"]
    if any(indicator in user_msg.lower() for indicator in unrealistic_indicators) and len(user_msg.strip()) > 50:
        return {
            "reply": f"While I appreciate your confidence, I want to challenge some assumptions here. What makes you think this will be [easy/simple/quick]? What data or experience supports this timeline? What's your contingency plan if things don't go as expected?",
            "web_search_status": {"is_searching": False, "query": None, "completed": False}
        }
    
    return None

def validate_question_answer(user_msg, session_data, history):
    """
    Enhanced validation with critiquing behaviors - challenge superficial answers
    and push for deeper thinking and specificity.
    Validate that user is not trying to skip questions in KYC and Business Plan phases
    """
    if not session_data:
        return None
    
    current_phase = session_data.get("current_phase", "")
    asked_q = session_data.get("asked_q", "")
    
    # Don't validate during initial startup (when asked_q is empty or initial)
    if not asked_q or asked_q in ["", "KYC.01", "BUSINESS_PLAN.01"]:
        return None
    
    # Only validate for KYC and Business Plan phases
    if current_phase not in ["KYC", "BUSINESS_PLAN"]:
        return None
    
    # Extract content from user_msg (could be dict or string)
    if isinstance(user_msg, dict):
        user_content = user_msg.get("content", "")
    else:
        user_content = str(user_msg)
    
    # Check if user is trying to use commands to skip questions
    user_msg_lower = user_content.lower().strip()
    
    # Commands that are allowed (these don't skip questions, they help answer them)
    # In KYC phase, disable all helper commands to force direct answers
    if current_phase == "KYC":
        blocked_commands = ["draft", "support", "scrapping:", "kickstart", "who do i contact?"]
        
        # Block these commands in KYC phase
        if any(user_msg_lower.startswith(cmd) for cmd in blocked_commands):
            return {
                "reply": f"""I understand you'd like to use helper tools, but during the KYC phase, it's important that you provide direct answers to help me understand your background and goals.

Please provide a direct answer to the current question. This will help me personalize your experience and provide the most relevant guidance for your specific situation.

The helper tools (Draft, Support, Scrapping, Kickstart, Contact) will be available in the Business Planning phase where they can be more helpful for complex business questions.

For now, please share your thoughts directly about the current question.""",
                "web_search_status": {"is_searching": False, "query": None, "completed": False}
            }
    else:
        # In other phases, allow these commands
        allowed_commands = ["draft", "support", "scrapping:", "kickstart", "who do i contact?"]
        
        # If user is using an allowed command, let them proceed
        if any(user_msg_lower.startswith(cmd) for cmd in allowed_commands):
            return None
    
    # Check for attempts to skip or manipulate the conversation
    skip_indicators = [
        "skip", "next", "move on", "continue", "go to next", "next question",
        "i don't want to answer", "i'll answer later", "not now", "maybe later",
        "i'm done", "finished", "complete", "that's enough", "no more questions"
    ]
    
    if any(indicator in user_msg_lower for indicator in skip_indicators):
        # Get the current question context
        current_question_num = "1"
        if "." in asked_q:
            try:
                current_question_num = asked_q.split(".")[1]
            except:
                pass
        
        # Create phase-specific message
        if current_phase == "KYC":
            help_message = """Please provide a direct answer to the current question. This will help me personalize your experience and provide the most relevant guidance for your specific situation."""
        else:
            help_message = """If you're unsure about how to answer, you can use:
- **Support** - for guided help with the question
- **Draft** - for me to help create an answer based on what you've shared so far"""
        
        return {
            "reply": f"""I understand you'd like to move forward, but it's important that we complete each question to ensure I can provide you with the best possible guidance.

We're currently on question {current_question_num} of the {current_phase} phase. Each question is designed to help me understand your specific situation and provide personalized advice.

Please provide an answer to the current question so we can continue building your comprehensive business plan together. Your detailed responses will help me tailor the guidance specifically for your needs.

{help_message}

Let's continue with the current question.""",
            "web_search_status": {"is_searching": False, "query": None, "completed": False}
        }
    
    # Check if user is asking clarifying questions about the current question (these are allowed)
    clarifying_questions = [
        "what question", "what is the question", "what do you want to know", "what should i answer",
        "what are you asking", "what is this question about", "can you repeat the question",
        "what do you need to know", "what information do you need", "what should i tell you"
    ]
    
    if any(clarifying_question in user_msg_lower for clarifying_question in clarifying_questions):
        # Allow clarifying questions - these help users understand what to answer
        return None
    
    # Check if user is trying to ask unrelated questions instead of answering
    unrelated_question_indicators = ["what is ai", "tell me about", "explain", "how does", "can you tell me about"]
    
    if user_msg_lower.endswith("?") and any(indicator in user_msg_lower for indicator in unrelated_question_indicators):
        # Create phase-specific message
        if current_phase == "KYC":
            help_message = """Please provide a direct answer to help me understand your situation better."""
        else:
            help_message = """If you need help with the current question, you can use:
- **Support** - for guided help with the question
- **Draft** - for me to help create an answer based on what you've shared so far"""
        
        return {
            "reply": f"""I appreciate your question! However, right now we're in the {current_phase} phase where I'm gathering information about you and your business to provide personalized guidance.

I'd be happy to answer your question once we complete the current question. For now, please provide an answer to help me understand your situation better.

{help_message}

Let's focus on answering the current question first.""",
            "web_search_status": {"is_searching": False, "query": None, "completed": False}
        }
    
    # Check if user is providing rating responses to non-rating questions
    if current_phase == "KYC":
        # Check if this looks like a rating response (numbers separated by commas)
        rating_pattern = r'^\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+$'
        if re.match(rating_pattern, user_content.strip()):
            # Only allow rating responses for KYC.07 (skills rating question)
            if asked_q != "KYC.07":
                return {
                    "reply": f"""I see you've provided a rating response, but the current question is asking about something different.

We're currently on question {asked_q.split('.')[1] if '.' in asked_q else 'unknown'} which asks: "{asked_q.replace('KYC.', '')}"

Please provide an answer that directly addresses the current question instead of rating responses.""",
                    "web_search_status": {"is_searching": False, "query": None, "completed": False}
                }
    
    # Check for very short or empty responses that might indicate skipping
    if len(user_content.strip()) < 3 and user_msg_lower not in ["yes", "no", "y", "n", "ok", "okay"]:
        # Different messages for KYC vs other phases
        if current_phase == "KYC":
            return {
                "reply": f"""I need a bit more information to help you effectively. Please provide a more detailed answer to the current question.

The more information you share, the better I can tailor my guidance to your specific situation and needs.

Please provide a more detailed response to continue.""",
                "web_search_status": {"is_searching": False, "query": None, "completed": False}
            }
        else:
            return {
                "reply": f"""I need a bit more information to help you effectively. Please provide a more detailed answer to the current question.

The more information you share, the better I can tailor my guidance to your specific situation and needs.

If you're unsure how to answer, you can use:
- **Support** - for guided help with the question
- **Draft** - for me to help create an answer based on what you've shared so far

Please provide a more detailed response to continue.""",
                "web_search_status": {"is_searching": False, "query": None, "completed": False}
            }
    
    return None

def validate_session_state(session_data, history):
    """Validate session state integrity to prevent question skipping"""
    if not session_data:
        return None
    
    current_phase = session_data.get("current_phase", "")
    asked_q = session_data.get("asked_q", "")
    answered_count = session_data.get("answered_count", 0)
    
    # Don't validate during initial startup (when asked_q is empty or initial)
    if not asked_q or asked_q in ["", "KYC.01", "BUSINESS_PLAN.01"]:
        return None
    
    # Only validate for KYC and Business Plan phases
    if current_phase not in ["KYC", "BUSINESS_PLAN"]:
        return None
    
    # Calculate expected answered count based on history
    expected_answered_count = len([pair for pair in history if pair.get("answer", "").strip()])
    
    # Check if answered_count is significantly behind (indicating skipped questions)
    # Only trigger if there's a major discrepancy (more than 2 questions behind)
    if answered_count < expected_answered_count - 2:
        # Create phase-specific message
        if current_phase == "KYC":
            help_message = """Please provide a complete answer to the current question so we can continue building your comprehensive business plan."""
        else:
            help_message = """If you need help with the current question, you can use:
- **Support** - for guided help with the question
- **Draft** - for me to help create an answer based on what you've shared so far"""
        
        return {
            "reply": f"""I notice there might be a discrepancy in our conversation history. To ensure I can provide you with the most accurate and personalized guidance, we need to make sure we've properly addressed all questions.

We're currently in the {current_phase} phase. Please provide a complete answer to the current question so we can continue building your comprehensive business plan.

Your detailed responses are essential for creating a tailored business strategy that addresses your specific needs and goals.

{help_message}

Let's continue with the current question.""",
            "web_search_status": {"is_searching": False, "query": None, "completed": False}
        }
    
    # Validate that asked_q is in the correct format and sequence
    if current_phase == "KYC":
        if not asked_q.startswith("KYC.") and asked_q != "KYC.19_ACK":
            return {
                "reply": f"""I need to ensure we're following the proper KYC sequence. Please provide an answer to the current KYC question so we can continue systematically building your business profile.

Each question in the KYC phase is designed to help me understand your background, experience, and goals. Skipping questions would prevent me from providing you with the most relevant and personalized guidance.

Please provide a detailed answer to the current question. This will help me personalize your experience and provide the most relevant guidance for your specific situation.

Let's continue with the current KYC question.""",
                "web_search_status": {"is_searching": False, "query": None, "completed": False}
            }
    
    elif current_phase == "BUSINESS_PLAN":
        if not asked_q.startswith("BUSINESS_PLAN."):
            return {
                "reply": f"""I need to ensure we're following the proper Business Plan sequence. Please provide an answer to the current business planning question so we can continue systematically developing your business strategy.

Each question in the Business Plan phase is designed to help create a comprehensive and actionable business plan tailored to your specific situation. Skipping questions would result in an incomplete plan that doesn't address all the necessary aspects of your business.

Please provide a detailed answer to the current question.

If you need help, you can use:
- **Support** - for guided help with the question
- **Draft** - for me to help create an answer based on what you've shared so far

Let's continue with the current business planning question.""",
                "web_search_status": {"is_searching": False, "query": None, "completed": False}
            }
    
    return None

async def get_angel_reply(user_msg, history, session_data=None):
    import time
    start_time = time.time()
    
    # Get user name from session data, fallback to generic greeting
    user_name = session_data.get("user_name", "there") if session_data else "there"
    
    # KYC completion check removed - now triggered immediately after final answer
    
    # Validate that user is not trying to skip questions
    validation_result = validate_question_answer(user_msg, session_data, history)
    if validation_result:
        return validation_result
    
    # Debug logging for session state
    if session_data:
        print(f"🔍 DEBUG - Session State: phase={session_data.get('current_phase')}, asked_q={session_data.get('asked_q')}, answered_count={session_data.get('answered_count')}")
    
    # Validate session state integrity
    session_validation = validate_session_state(session_data, history)
    if session_validation:
        print(f"🔍 DEBUG - Session validation triggered: {session_validation.get('reply', '')[:100]}...")
        return session_validation
    
    # Provide critiquing feedback for superficial or unrealistic answers
    if user_msg and user_msg.get("content"):
        critique_feedback = provide_critiquing_feedback(user_msg["content"], session_data, history)
        if critique_feedback:
            print(f"🔍 DEBUG - Critiquing feedback triggered: {critique_feedback.get('reply', '')[:100]}...")
            return critique_feedback
    
    # Define formatting instruction at the top to avoid UnboundLocalError
    FORMATTING_INSTRUCTION = f"""
CRITICAL FORMATTING RULES - FOLLOW EXACTLY:

1. ALWAYS start with a brief acknowledgment (1-2 sentences max)
2. Add a blank line for visual separation
3. Present the question in a clear, structured format:

For YES/NO questions:
"That's great, {user_name}!

Have you started a business before?
• Yes
• No"

For multiple choice questions:
"That's perfect, {user_name}!

What's your current work situation?
• Full-time employed
• Part-time
• Student
• Unemployed
• Self-employed/freelancer
• Other"

IMPORTANT: ALWAYS use regular bullets (•) for multiple choice options, NEVER use circle bullets (○)

For rating questions:
"That's helpful, {user_name}!

How comfortable are you with business planning?
○ ○ ○ ○ ○
1  2  3  4  5"

For verification steps:
"That's excellent, {user_name}!

Here's what I've captured so far:
[Summary of information]

Does this look accurate to you? If not, please let me know where you'd like to modify and we'll work through this some more."

❌ NEVER DO THIS: 
"What's your current work situation? Full-time employed Part-time Student Unemployed Self-employed/freelancer Other"
"Have you started a business before? Yes / No"

✅ ALWAYS DO THIS: 
"What's your current work situation?
• Full-time employed
• Part-time
• Student
• Unemployed
• Self-employed/freelancer
• Other"

"Have you started a business before?
• Yes
• No"

CRITICAL: Use regular bullets (•) for ALL multiple choice options, never circle bullets (○)

BUSINESS PLAN SPECIFIC RULES:
• Ask ONE question at a time in EXACT sequential order
• After every 3-4 questions, provide verification step
• Wait for user acknowledgment before proceeding
• Never combine questions or skip verification steps
• Each question must be on its own line with proper spacing
• Use verification format: "Here's what I've captured so far: [summary]. Does this look accurate to you?"
• NEVER mold user answers into mission, vision, USP without explicit verification
• Start with BUSINESS_PLAN.01 and proceed sequentially
• Do NOT jump to later questions or combine multiple questions

VERIFICATION FLOW REQUIREMENTS:
• When providing verification, ONLY show the verification message
• Do NOT combine verification with the next question
• Wait for user response (Accept/Modify) before proceeding
• After user accepts, show brief acknowledgment: "Great! Let's move to the next question..."
• Then ask the next sequential question

CRITIQUING SYSTEM (50/50 APPROACH):
• **50% Positive Acknowledgment**: Always start with supportive, encouraging response to their answer
• **50% Educational Coaching**: Identify opportunities to coach the user based on their information
• **Critiquing Guidelines**: 
  - Don't be critical, but critique their answer constructively
  - Offer insightful information that helps them better understand the business space they're entering
  - Provide high-value education that pertains to their answer and business field
  - Include specific examples, best practices, and actionable insights
  - Focus on opportunities and growth rather than problems
• Example: "Social media influencing is a very popular field. Some of the most successful influencers cross-post to different platforms like YouTube, Threads, etc. to ensure reach and expand their audiences. Podcasts are also an interesting medium that has gained significant popularity in recent years."

Do NOT include question numbers, progress percentages, or step counts in your response.
"""
    
    # Handle empty input based on context
    if not user_msg.get("content") or user_msg["content"].strip() == "":
        # If we're revisiting business plan, continue with current question
        if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
            current_tag = session_data.get("asked_q", "BUSINESS_PLAN.01")
            if current_tag and current_tag.startswith("BUSINESS_PLAN."):
                # Generate the current question
                question_prompt = f"""
                Generate the business plan question for tag: {current_tag}
                
                Make sure to:
                1. Ask the appropriate business plan question for this tag
                2. Include the proper tag: [[Q:{current_tag}]]
                3. Use structured format with proper line breaks
                4. Provide context if this is a verification or continuation
                """
                
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": ANGEL_SYSTEM_PROMPT},
                        {"role": "system", "content": TAG_PROMPT},
                        {"role": "system", "content": FORMATTING_INSTRUCTION},
                        {"role": "user", "content": question_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                return response.choices[0].message.content
        
        # Default to "hi" for other cases
        user_msg["content"] = "hi"

    user_content = user_msg["content"].strip()
    print(f"🚀 Starting Angel reply generation for: {user_content[:50]}...")
    
    # KYC completion check moved to AFTER AI response generation
    
    # Check if Business Plan phase is complete (question 46 for full flow)
    if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        current_tag = session_data.get("asked_q", "")
        if current_tag and current_tag.startswith("BUSINESS_PLAN."):
            try:
                question_num = int(current_tag.split(".")[1])
                if question_num >= 46:  # Business Plan complete (restored to full 46 questions)
                    return await handle_business_plan_completion(session_data, history)
            except (ValueError, IndexError):
                pass
    
    # Handle Accept response for verification
    if user_content.lower() == "accept":
        # Check if we're in a verification flow
        if session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
            # Move to next question in business plan
            current_tag = session_data.get("asked_q", "BUSINESS_PLAN.01")
            if current_tag and current_tag.startswith("BUSINESS_PLAN."):
                try:
                    current_num = int(current_tag.split(".")[1])
                    next_num = current_num + 1
                    next_tag = f"BUSINESS_PLAN.{next_num:02d}"
                    
                    # Check if we've reached the end of business plan questions
                    if next_num > 46:  # Business plan is complete (restored to full 46 questions)
                        # Business plan is complete, trigger completion
                        return await handle_business_plan_completion(session_data, history)
                    
                    # Generate next question
                    next_question_prompt = f"""
                    The user has accepted the verification for business plan question {current_tag}. 
                    Now move to the next business plan question: {next_tag}
                    
                    Generate the next business plan question in the sequence. Make sure to:
                    1. Acknowledge their acceptance briefly (1-2 sentences)
                    2. Ask the next sequential business plan question
                    3. Include the proper tag: [[Q:{next_tag}]]
                    4. Use structured format with proper line breaks
                    5. Make it feel like a natural continuation of the business planning process
                    """
                    
                    response = await client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": ANGEL_SYSTEM_PROMPT},
                            {"role": "system", "content": TAG_PROMPT},
                            {"role": "system", "content": FORMATTING_INSTRUCTION},
                            {"role": "user", "content": next_question_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    # Return the response with session update info
                    return {
                        "reply": response.choices[0].message.content,
                        "patch_session": {
                            "asked_q": next_tag,
                            "answered_count": session_data.get("answered_count", 0) + 1
                        }
                    }
                except (ValueError, IndexError):
                    pass
        
        # For other cases, let the normal flow handle it
        # Don't return a fallback here - let the main AI generation handle the response
    
    # Add instruction for proper question formatting
    
    # Check if web search is needed based on session phase and content
    needs_web_search = False
    web_search_query = None
    competitor_research_requested = False
    
    # Check for WEBSEARCH_QUERY trigger from scrapping command
    if "WEBSEARCH_QUERY:" in user_content:
        needs_web_search = True
        web_search_query = user_content.split("WEBSEARCH_QUERY:")[1].strip()
        print(f"🔍 Web search triggered by scrapping command: {web_search_query}")
    
    elif session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        # Look for competitive analysis, market research, or vendor recommendation needs
        business_keywords = ["competitors", "market", "industry", "trends", "pricing", "vendors", "domain", "legal requirements"]
        if any(keyword in user_content.lower() for keyword in business_keywords):
            needs_web_search = True
            
            # Extract or generate search query with previous calendar year
            current_year = datetime.now().year
            previous_year = current_year - 1
            
            # ENHANCED COMPETITOR RESEARCH DETECTION
            competitor_keywords = ["competitors", "competition", "main competitors", "who are my competitors", "competing companies", "rival companies"]
            if any(keyword in user_content.lower() for keyword in competitor_keywords):
                competitor_research_requested = True
                web_search_query = f"main competitors in {session_data.get('industry', 'business')} industry {previous_year}"
            elif "market" in user_content.lower() or "trends" in user_content.lower():
                web_search_query = f"market trends {session_data.get('industry', 'business')} {session_data.get('location', '')} {previous_year}"
            elif "domain" in user_content.lower():
                web_search_query = "domain registration availability check websites"
            elif "wine" in user_content.lower() or "influencer" in user_content.lower():
                web_search_query = f"top wine influencers on social media {previous_year}"
    
    # Conduct web search if needed
    search_results = ""
    web_search_status = {"is_searching": False, "query": None}
    immediate_response = None
    
    if needs_web_search and web_search_query:
        # Set web search status for progress indicator
        web_search_status = {"is_searching": True, "query": web_search_query}
        
        # Provide immediate feedback to user
        immediate_response = f"I'm conducting some background research on '{web_search_query}' to provide you with the most current information. This will just take a moment..."
        
        # ENHANCED COMPETITOR RESEARCH HANDLING
        if competitor_research_requested:
            # Extract business context for comprehensive competitor research
            business_context = extract_business_context_from_history(history)
            if session_data:
                business_context.update({
                    "industry": session_data.get("industry", ""),
                    "location": session_data.get("location", ""),
                    "business_name": session_data.get("business_name", ""),
                    "business_type": session_data.get("business_type", "")
                })
            
            # Conduct comprehensive competitor research
            competitor_research_result = await handle_competitor_research_request(user_content, business_context, history)
            
            if competitor_research_result.get("success"):
                search_results = f"\n\n🔍 **Comprehensive Competitor Research Results:**\n\n{competitor_research_result['analysis']}\n\n*Research conducted using {competitor_research_result['research_sources']} authoritative sources*"
            else:
                # Fallback to regular web search
                search_start = time.time()
                search_results = await conduct_web_search(web_search_query)
                search_time = time.time() - search_start
                print(f"🔍 Web search completed in {search_time:.2f} seconds")
                
                if search_results and "unable to conduct web research" not in search_results:
                    search_results = f"\n\nResearch Results:\n{search_results}"
        else:
            # Regular web search for non-competitor requests
            search_start = time.time()
            search_results = await conduct_web_search(web_search_query)
            search_time = time.time() - search_start
            print(f"🔍 Web search completed in {search_time:.2f} seconds")
            
            if search_results and "unable to conduct web research" not in search_results:
                search_results = f"\n\nResearch Results:\n{search_results}"
        
        # Update status to completed
        web_search_status = {"is_searching": False, "query": web_search_query, "completed": True}

    # Check if this is a command that should not generate new questions
    is_command_response = user_content.lower() in ["draft", "support", "scrapping", "scraping", "draft more"] or user_content.lower().startswith("scrapping:")
    
    # For commands, bypass AI generation and provide direct responses
    if is_command_response and session_data and session_data.get("current_phase") == "BUSINESS_PLAN":
        print(f"🔧 Command detected: {user_content.lower()} - bypassing AI generation to prevent question skipping")
        
        # Generate direct command response without AI
        if user_content.lower() == "draft":
            reply_content = handle_draft_command("", history, session_data)
        elif user_content.lower().startswith("scrapping:"):
            notes = user_content[10:].strip()
            reply_content = handle_scrapping_command("", notes, history, session_data)
        elif user_content.lower() in ["scrapping", "scraping"]:
            reply_content = handle_scrapping_command("", "", history, session_data)
        elif user_content.lower() == "support":
            reply_content = handle_support_command("", history, session_data)
        elif user_content.lower() == "draft more":
            reply_content = handle_draft_more_command("", history, session_data)
        else:
            # Fallback to normal AI generation
            reply_content = "I understand you'd like to use a command. Please try again."
        
        # Return the command response directly without further processing
        return {
            "reply": reply_content,
            "web_search_status": {"is_searching": False, "query": None, "completed": False},
            "immediate_response": None
        }
    
    # Build messages for OpenAI - optimized for speed
    msgs = [
        {"role": "system", "content": ANGEL_SYSTEM_PROMPT},
        {"role": "system", "content": TAG_PROMPT},
        {"role": "system", "content": FORMATTING_INSTRUCTION}
    ]
    
    # Only add web search prompt if web search was conducted
    if search_results:
        msgs.append({"role": "system", "content": WEB_SEARCH_PROMPT})
    
    # Add search results and immediate response if available
    if search_results:
        msgs.append({
            "role": "system", 
            "content": f"Web search results for your reference:\n{search_results}\n\nIntegrate relevant findings naturally into your response."
        })
    
    # Add immediate response instruction if web search was conducted
    if immediate_response:
        msgs.append({
            "role": "system",
            "content": f"IMPORTANT: The user has requested research and search results have been provided above. You MUST include the research findings in your response. Do not just acknowledge the research - provide the actual results and answer their question based on the search findings. The user expects to get the research results immediately, not just a notification that research is being conducted."
        })
    
    # Add conversation history (trimmed for performance) and current message
    trimmed_history = trim_conversation_history(history, max_messages=10)
    msgs.extend(trimmed_history)
    msgs.append({"role": "user", "content": user_content})

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=msgs,
        temperature=0.7,
        max_tokens=1000,  # Limit response length for faster processing
        stream=False  # Ensure non-streaming for consistent response times
    )

    reply_content = response.choices[0].message.content
    
    # Handle remaining commands (kickstart, contact) that weren't processed earlier
    current_phase = session_data.get("current_phase", "") if session_data else ""
    
    if current_phase != "KYC":
        # Only process remaining commands outside of KYC phase
        if user_content.lower() == "kickstart":
            reply_content = handle_kickstart_command(reply_content, history, session_data)
        elif user_content.lower() == "who do i contact?":
            reply_content = handle_contact_command(reply_content, history, session_data)
    
    # Inject missing tag if AI forgot to include one
    reply_content = inject_missing_tag(reply_content, session_data)
    
    # Check if AI response contains WEBSEARCH_QUERY (from scrapping command)
    if "WEBSEARCH_QUERY:" in reply_content:
        needs_web_search = True
        web_search_query = reply_content.split("WEBSEARCH_QUERY:")[1].strip()
        print(f"🔍 Web search triggered by AI response: {web_search_query}")
        # Remove the WEBSEARCH_QUERY from the response
        reply_content = reply_content.split("WEBSEARCH_QUERY:")[0].strip()
    
    # Format response structure to use proper list format instead of paragraph
    reply_content = format_response_structure(reply_content)
    
    # Ensure questions are properly separated
    reply_content = ensure_question_separation(reply_content, session_data)
    
    # Validate business plan question sequence
    reply_content = validate_business_plan_sequence(reply_content, session_data)
    
    # Fix verification flow to separate verification from next question
    reply_content = fix_verification_flow(reply_content, session_data)
    
    # Prevent AI from molding user answers without verification
    reply_content = prevent_ai_molding(reply_content, session_data)
    
    # Add critiquing insights based on user's business field
    reply_content = add_critiquing_insights(reply_content, session_data, user_content)
    
    # Suggest using Draft if user has already provided relevant information
    reply_content = suggest_draft_if_relevant(reply_content, session_data, user_content, history)
    
    # Add proactive support guidance based on identified areas needing help
    reply_content = add_proactive_support_guidance(reply_content, session_data, history)
    
    # Check if we need to provide a section summary
    current_tag = session_data.get("asked_q") if session_data else None
    section_summary_info = check_for_section_summary(current_tag, session_data, history)
    
    if section_summary_info:
        # Add section summary requirements to the system prompt
        summary_instruction = f"""
IMPORTANT: You have just completed {section_summary_info['section_name']} section. 
You MUST provide a comprehensive section summary that includes:

1. **Summary**: Recap the key information provided in this section
2. **Educational Insights**: Provide valuable insights about this business area
3. **Critical Considerations**: Highlight important watchouts and considerations for this business type
4. **Verification Request**: Ask user to verify the information before proceeding

Use this format:
"🎯 **{section_summary_info['section_name']} Section Complete**

**Summary of Your Information:**
[Recap key points from this section]

**Educational Insights:**
[Provide valuable business insights related to this section]

**Critical Considerations:**
[Highlight important watchouts and things to consider]

**Verification:**
Here's what I've captured so far: [summary]. Does this look accurate to you? If not, please let me know where you'd like to modify and we'll work through this some more."
"""
        # Add this instruction to the messages
        msgs.append({"role": "system", "content": summary_instruction})
        
        # Regenerate the response with section summary
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=msgs,
            temperature=0.7,
            max_tokens=1000,
            stream=False
        )
        reply_content = response.choices[0].message.content
    
    # Ensure proper question formatting with line breaks and structure
    reply_content = ensure_proper_question_formatting(reply_content, session_data)

    end_time = time.time()
    response_time = end_time - start_time
    print(f"⏱️ Angel reply generated in {response_time:.2f} seconds")
    
    # Check if user just answered the final KYC question
    if session_data and session_data.get("current_phase") == "KYC":
        current_tag = session_data.get("asked_q", "")
        if current_tag and current_tag.startswith("KYC."):
            try:
                question_num = int(current_tag.split(".")[1])
                # Check if user just answered the final question (19) with "proactive" or "non-proactive" response
                if (question_num == 19 and 
                    not current_tag.endswith("_ACK") and
                    ("proactive" in user_content.lower() or 
                     user_content.lower().strip() in ["yes", "y", "yeah", "yep", "sure", "ok", "okay", "absolutely", "definitely", "no", "n", "nope", "NO", "NOPE" , "proactive" , "Proactive" , "excellent" , "Excellent" , "fantastic" , "Fantastic" , "congratulations" , "Congratulations"] or
                     "yes" in user_content.lower() or
                     "no" in user_content.lower())):
                    
                    print(f"🎯 User answered final KYC question (19) - triggering completion immediately")
                    # Trigger completion immediately after acknowledgment
                    return await handle_kyc_completion(session_data, history)
            except (ValueError, IndexError):
                pass
    
    return {
        "reply": reply_content,
        "web_search_status": web_search_status,
        "immediate_response": immediate_response
    }

def handle_draft_command(reply, history, session_data=None):
    """Handle the Draft command with comprehensive response generation"""
    # Extract context from conversation history
    context_summary = extract_conversation_context(history)
    business_context = extract_business_context_from_history(history)
    
    # Get current question context for more targeted responses
    current_question = get_current_question_context(history)
    
    # Generate draft content based on conversation history and current question
    draft_content = generate_draft_content(history, business_context, current_question)
    
    # Create a comprehensive draft response
    draft_response = f"{draft_content}\n\n"
    
    # Add verification trigger to show Accept/Modify buttons
    draft_response += "**Verification:**\n"
    draft_response += "Here's what I've captured so far: "
    
    # Extract key information for verification - use session data if available
    business_name = ""
    if session_data and session_data.get("title"):
        business_name = session_data["title"]
    elif business_context.get("business_name"):
        business_name = business_context["business_name"]
    
    if business_name:
        draft_response += f"{business_name} "
    
    # Add complete context from the draft (no truncation)
    draft_response += f"with a draft response covering {get_question_topic(current_question)}. Does this look accurate to you?\n\n"
    
    draft_response += "If not, please let me know where you'd like to modify, and we'll work through this some more."
    
    return draft_response

def get_current_question_context(history):
    """Extract the current question context from the most recent assistant message"""
    # Look for the most recent assistant message that contains a question tag
    for msg in reversed(history[-8:]):  # Look at last 8 messages to find the actual question
        if msg.get('role') == 'assistant' and msg.get('content'):
            content = msg['content'].lower()
            # Skip command responses and look for actual questions
            if any(command in content for command in ['here\'s a draft', 'let\'s work through this', 'here\'s a refined version', 'verification:', 'here\'s what i\'ve captured']):
                continue
            # Look for question tags or question indicators
            if '[[' in content and ']]' in content and any(indicator in content for indicator in ['what', 'how', 'when', 'where', 'why', 'do you', 'are you', 'can you']):
                question_text = content
                print(f"🔍 DEBUG - Found current question: {question_text[:200]}...")
                return question_text
    print("🔍 DEBUG - No question found in recent history")
    return ""

def get_question_topic(current_question):
    """Extract the main topic from the current question"""
    if not current_question:
        print("🔍 DEBUG - No current question provided to get_question_topic")
        return "business planning"
    
    if any(keyword in current_question for keyword in ['problem does your business solve', 'who has this problem', 'problem', 'solve', 'pain point', 'need']):
        print("🔍 DEBUG - Detected problem-solution topic")
        return "problem-solution fit"
    elif any(keyword in current_question for keyword in ['competitor', 'competition', 'main competitors', 'strengths and weaknesses', 'competitive advantage', 'unique value proposition', 'what makes your business unique']):
        print("🔍 DEBUG - Detected competitive analysis topic")
        return "competitive analysis"
    elif any(keyword in current_question for keyword in ['target market', 'demographics', 'psychographics', 'behaviors', 'ideal customer']):
        print("🔍 DEBUG - Detected target market topic")
        return "target market definition"
    elif any(keyword in current_question for keyword in ['location', 'space', 'facility', 'equipment', 'infrastructure', 'where will your business be located']):
        print("🔍 DEBUG - Detected operational requirements topic")
        return "operational requirements"
    elif any(keyword in current_question for keyword in ['staff', 'hiring', 'team', 'employee', 'operational needs', 'initial staff']):
        print("🔍 DEBUG - Detected staffing needs topic")
        return "staffing needs"
    elif any(keyword in current_question for keyword in ['supplier', 'vendor', 'partner', 'relationship', 'key partners']):
        print("🔍 DEBUG - Detected supplier relationships topic")
        return "supplier and vendor relationships"
    elif any(keyword in current_question for keyword in ['key features and benefits', 'how does it work', 'main components', 'steps involved', 'value or results', 'product', 'service', 'core offering', 'what will you be offering']):
        print("🔍 DEBUG - Detected core product/service topic")
        return "core product or service"
    elif any(keyword in current_question for keyword in ['mission', 'tagline', 'mission statement', 'business stands for']):
        print("🔍 DEBUG - Detected mission statement topic")
        return "mission statement"
    elif any(keyword in current_question for keyword in ['sales', 'projected sales', 'first year', 'sales projections', 'revenue', 'income']):
        print("🔍 DEBUG - Detected sales projections topic")
        return "sales projections"
    elif any(keyword in current_question for keyword in ['startup costs', 'estimated startup costs', 'one-time expenses', 'initial costs', 'launch costs']):
        print("🔍 DEBUG - Detected startup costs topic")
        return "startup costs"
    elif any(keyword in current_question for keyword in ['financial', 'budget', 'costs', 'expenses', 'funding', 'investment']):
        print("🔍 DEBUG - Detected financial planning topic")
        return "financial planning"
    elif any(keyword in current_question for keyword in ['intellectual property', 'patents', 'trademarks', 'copyrights', 'proprietary technology', 'unique processes', 'formulas', 'legal protections']):
        print("🔍 DEBUG - Detected intellectual property topic")
        return "intellectual property"
    elif any(keyword in current_question for keyword in ['product development timeline', 'working prototype', 'mvp', 'milestones', 'launch', 'validate your concept', 'full development']):
        print("🔍 DEBUG - Detected product development topic")
        return "product development"
    else:
        print("🔍 DEBUG - No specific topic detected, using default business planning")
        return "business planning"

def generate_draft_content(history, business_context, current_question=""):
    """Generate draft content based on conversation history"""
    # Extract recent messages (both user and assistant) to understand context
    recent_messages = []
    for msg in history[-8:]:  # Look at last 8 messages (4 exchanges)
        if msg.get('content'):
            recent_messages.append(msg['content'])
    
    # Debug logging
    print(f"🔍 DEBUG - Recent messages for draft context: {recent_messages}")
    
    # Generate contextual draft based on what they've been discussing
    if not recent_messages:
        return "Based on our conversation, here's a draft response that captures the key points we've discussed and provides a comprehensive answer to your current question."
    
    # Look for key topics in recent messages (both questions and responses)
    recent_text = " ".join(recent_messages).lower()
    print(f"🔍 DEBUG - Recent text for draft analysis: {recent_text[:200]}...")
    
    # Use the current_question parameter if provided, otherwise extract from history
    if not current_question:
        current_question = get_current_question_context(history)
    
    print(f"🔍 DEBUG - Current question context for draft: {current_question[:100]}...")
    
    # Check for specific business plan question topics based on current question
    if any(keyword in current_question for keyword in ['problem does your business solve', 'who has this problem', 'problem', 'solve', 'pain point', 'need']):
        return "Based on your business vision, here's a draft for your problem-solution fit: Your business solves [specific problem] for [target audience] who experience [pain point description]. This problem is significant because [impact/urgency explanation]. Your solution addresses this by [solution approach], providing [key benefits] that directly alleviate the pain point. Consider the frequency and severity of this problem, the current alternatives available, and why your solution is uniquely positioned to address it effectively. Focus on clearly articulating the problem, who experiences it, and how your business provides a superior solution."
    
    elif any(keyword in current_question for keyword in ['competitor', 'competition', 'main competitors', 'strengths and weaknesses', 'competitive advantage', 'unique value proposition', 'what makes your business unique']):
        return "Based on your business context, here's a draft analysis of your competitive landscape: Your main competitors likely include established players in your industry who offer similar solutions. Consider analyzing their strengths (brand recognition, resources, market share) and weaknesses (pricing, customer service, innovation gaps). Your competitive advantage should focus on what makes your solution unique - whether it's better pricing, superior customer experience, innovative features, or specialized expertise. Focus on identifying 3-5 key competitors and analyzing their market positioning, pricing models, and customer base."
    
    elif any(keyword in current_question for keyword in ['target market', 'demographics', 'psychographics', 'behaviors', 'ideal customer']):
        return "Based on your business goals, here's a draft for your target market: Your ideal customers are likely [demographic profile] who value [key benefits] and are looking for [specific solutions]. Consider their demographics (age, income, location), psychographics (interests, values, lifestyle), and behaviors (buying patterns, preferences). Focus on creating detailed customer personas and understanding their pain points and needs. Think about how you can reach and connect with this audience effectively through appropriate channels and messaging."
    
    elif any(keyword in current_question for keyword in ['location', 'space', 'facility', 'equipment', 'infrastructure', 'where will your business be located']):
        return "Based on your business needs, here's a draft for your operational requirements: Your business location should be strategically chosen to maximize accessibility for your target customers while considering operational efficiency. Key factors include proximity to suppliers, transportation access, zoning requirements, and cost considerations. Your space and equipment needs should align with your business operations, ensuring you have adequate facilities to serve your customers effectively while maintaining operational efficiency. Focus on factors like zoning, transportation access, costs, and scalability."
    
    elif any(keyword in current_question for keyword in ['staff', 'hiring', 'team', 'employee', 'operational needs', 'initial staff']):
        return "Based on your business goals, here's a draft for your staffing needs: Your short-term operational needs should focus on identifying critical roles required for launch, including key personnel who can drive your core business functions. Consider hiring initial staff who bring essential skills and experience, securing appropriate workspace, and establishing operational processes. Prioritize roles that directly impact customer experience and business operations, ensuring you have the right team in place to execute your business plan effectively. Focus on identifying key positions, required qualifications, and your hiring timeline."
    
    elif any(keyword in current_question for keyword in ['supplier', 'vendor', 'partner', 'relationship', 'key partners']):
        return "Based on your business requirements, here's a comprehensive draft for your supplier and vendor relationships: You'll need to identify key suppliers and vendors who can provide essential products, services, or resources for your business operations. Consider building relationships with reliable partners who offer competitive pricing, quality products, and consistent service. Key partners might include suppliers for raw materials, service providers for essential business functions, and strategic partners who can help you reach your target market or enhance your offerings. Focus on reliability, quality, pricing, and long-term partnership potential. Evaluate potential partners based on their track record, financial stability, capacity to meet your needs, and alignment with your business values. Consider backup suppliers to ensure business continuity and negotiate favorable terms that support your growth objectives."
    
    elif any(keyword in current_question for keyword in ['key features and benefits', 'how does it work', 'main components', 'steps involved', 'value or results']):
        return "Based on your business vision, here's a draft for your key features and benefits: Your product/service offers [specific features] that provide [key benefits] to customers. The main components include [component 1], [component 2], and [component 3]. Customers will experience [specific outcomes] through a process that involves [step 1], [step 2], and [step 3]. Focus on clearly articulating the technical aspects, user experience, and measurable results customers can expect from using your solution."
    
    elif any(keyword in current_question for keyword in ['product', 'service', 'core offering', 'what will you be offering']):
        return "Based on your business vision, here's a draft for your core product or service: Your core offering is [product/service description] designed to [key benefits]. Consider what specific features, benefits, or outcomes customers will receive and how customers will interact with or use your product/service. Focus on your unique value proposition and how you'll deliver exceptional customer experience. Think about the key features that differentiate you from competitors and the specific outcomes customers can expect."
    
    elif any(keyword in current_question for keyword in ['mission', 'tagline', 'mission statement', 'business stands for']):
        return "Based on your business vision, here's a draft mission statement: [Business name] aims to [core purpose] by [key approach] to [target outcome]. Consider what your business stands for and how you would describe it in one compelling sentence. Think about your core values, purpose, and what makes you unique. Focus on creating a clear, inspiring statement that guides your business decisions and resonates with your target audience."
    
    elif any(keyword in current_question for keyword in ['sales', 'projected sales', 'first year', 'sales projections', 'revenue', 'income']):
        return "Based on your business goals, here's a draft for your first-year sales projections: Your projected sales for the first year should be based on realistic market analysis and conservative estimates. Consider factors like your target market size, customer acquisition rate, pricing strategy, and seasonal variations. Focus on creating projections that account for market penetration, customer lifetime value, and repeat business. Think about how you'll reach customers and what conversion rates you can realistically expect based on industry benchmarks and your marketing capabilities."
    
    elif any(keyword in current_question for keyword in ['startup costs', 'estimated startup costs', 'one-time expenses', 'initial costs', 'launch costs']):
        return "Based on your business needs, here's a draft for your startup costs: Your estimated startup costs should include essential one-time expenses like equipment purchases, initial inventory, legal fees, permits and licenses, website development, initial marketing campaigns, and office setup. Consider both essential startup costs and optional investments that could be deferred to manage cash flow. Focus on creating a comprehensive list of all one-time expenses needed to launch your business, including equipment, technology, legal requirements, and initial marketing. Think about equipment leasing vs. buying, bulk purchasing discounts, and phased implementation to optimize your startup investment."
    
    elif any(keyword in current_question for keyword in ['financial', 'budget', 'costs', 'expenses', 'funding', 'investment']):
        return "Based on your business requirements, here's a draft for your financial planning: Your financial plan should include startup costs, operating expenses, cash flow projections, and funding requirements. Consider fixed costs (rent, salaries, equipment) and variable costs (materials, marketing, commissions). Focus on creating realistic budgets, identifying funding sources, and planning for financial sustainability. Think about break-even analysis, profit margins, and financial contingency planning to ensure long-term viability."
    
    elif any(keyword in current_question for keyword in ['intellectual property', 'patents', 'trademarks', 'copyrights', 'proprietary technology', 'unique processes', 'formulas', 'legal protections']):
        return "Based on your business needs, here's a draft for your intellectual property strategy: Your business may have intellectual property assets including [patents/trademarks/copyrights] that protect your [unique processes/formulas/technology]. Consider what legal protections are important for your business, including patent applications for innovative processes, trademark registration for your brand, and copyright protection for original content. Focus on identifying your proprietary assets, understanding the legal requirements for protection, and developing a strategy to safeguard your competitive advantages."
    
    elif any(keyword in current_question for keyword in ['product development timeline', 'working prototype', 'mvp', 'milestones', 'launch', 'validate your concept', 'full development']):
        return "Based on your business goals, here's a draft for your product development timeline: Your development timeline should include key milestones such as [prototype development], [MVP creation], [testing and validation], and [full product launch]. Consider what working prototype or MVP you currently have and what milestones you need to reach before launch. Focus on creating a realistic timeline that accounts for development phases, testing periods, and validation steps. Think about how you'll validate your concept before full development and what resources you'll need at each stage."
    
    # Fallback to analyzing recent text if current question doesn't match
    elif any(keyword in recent_text for keyword in ['problem does your business solve', 'who has this problem', 'problem', 'solve', 'pain point', 'need']):
        return "Based on your business vision, here's a draft for your problem-solution fit: Your business solves [specific problem] for [target audience] who experience [pain point description]. This problem is significant because [impact/urgency explanation]. Your solution addresses this by [solution approach], providing [key benefits] that directly alleviate the pain point. Consider the frequency and severity of this problem, the current alternatives available, and why your solution is uniquely positioned to address it effectively. Focus on clearly articulating the problem, who experiences it, and how your business provides a superior solution."
    
    elif any(keyword in recent_text for keyword in ['competitor', 'competition', 'main competitors', 'strengths and weaknesses', 'competitive advantage', 'unique value proposition', 'what makes your business unique']):
        return "Based on your business context, here's a draft analysis of your competitive landscape: Your main competitors likely include established players in your industry who offer similar solutions. Consider analyzing their strengths (brand recognition, resources, market share) and weaknesses (pricing, customer service, innovation gaps). Your competitive advantage should focus on what makes your solution unique - whether it's better pricing, superior customer experience, innovative features, or specialized expertise. Focus on identifying 3-5 key competitors and analyzing their market positioning, pricing models, and customer base."
    
    elif any(keyword in recent_text for keyword in ['target market', 'demographics', 'psychographics', 'behaviors', 'ideal customer']):
        return "Based on your business goals, here's a draft for your target market: Your ideal customers are likely [demographic profile] who value [key benefits] and are looking for [specific solutions]. Consider their demographics (age, income, location), psychographics (interests, values, lifestyle), and behaviors (buying patterns, preferences). Focus on creating detailed customer personas and understanding their pain points and needs. Think about how you can reach and connect with this audience effectively through appropriate channels and messaging."
    
    elif any(keyword in recent_text for keyword in ['location', 'space', 'facility', 'equipment', 'infrastructure', 'where will your business be located']):
        return "Based on your business needs, here's a draft for your operational requirements: Your business location should be strategically chosen to maximize accessibility for your target customers while considering operational efficiency. Key factors include proximity to suppliers, transportation access, zoning requirements, and cost considerations. Your space and equipment needs should align with your business operations, ensuring you have adequate facilities to serve your customers effectively while maintaining operational efficiency. Focus on factors like zoning, transportation access, costs, and scalability."
    
    elif any(keyword in recent_text for keyword in ['staff', 'hiring', 'team', 'employee', 'operational needs', 'initial staff']):
        return "Based on your business goals, here's a draft for your staffing needs: Your short-term operational needs should focus on identifying critical roles required for launch, including key personnel who can drive your core business functions. Consider hiring initial staff who bring essential skills and experience, securing appropriate workspace, and establishing operational processes. Prioritize roles that directly impact customer experience and business operations, ensuring you have the right team in place to execute your business plan effectively. Focus on identifying key positions, required qualifications, and your hiring timeline."
    
    elif any(keyword in recent_text for keyword in ['supplier', 'vendor', 'partner', 'relationship', 'key partners']):
        return "Based on your business requirements, here's a draft for your supplier and vendor relationships: You'll need to identify key suppliers and vendors who can provide essential products, services, or resources for your business operations. Consider building relationships with reliable partners who offer competitive pricing, quality products, and consistent service. Key partners might include suppliers for raw materials, service providers for essential business functions, and strategic partners who can help you reach your target market or enhance your offerings. Focus on reliability, quality, pricing, and long-term partnership potential."
    
    elif any(keyword in recent_text for keyword in ['key features and benefits', 'how does it work', 'main components', 'steps involved', 'value or results']):
        return "Based on your business vision, here's a draft for your key features and benefits: Your product/service offers [specific features] that provide [key benefits] to customers. The main components include [component 1], [component 2], and [component 3]. Customers will experience [specific outcomes] through a process that involves [step 1], [step 2], and [step 3]. Focus on clearly articulating the technical aspects, user experience, and measurable results customers can expect from using your solution."
    
    elif any(keyword in recent_text for keyword in ['product', 'service', 'core offering', 'what will you be offering']):
        return "Based on your business vision, here's a draft for your core product or service: Your core offering is [product/service description] designed to [key benefits]. Consider what specific features, benefits, or outcomes customers will receive and how customers will interact with or use your product/service. Focus on your unique value proposition and how you'll deliver exceptional customer experience. Think about the key features that differentiate you from competitors and the specific outcomes customers can expect."
    
    elif any(keyword in recent_text for keyword in ['intellectual property', 'patents', 'trademarks', 'copyrights', 'proprietary technology', 'unique processes', 'formulas', 'legal protections']):
        return "Based on your business needs, here's a draft for your intellectual property strategy: Your business may have intellectual property assets including [patents/trademarks/copyrights] that protect your [unique processes/formulas/technology]. Consider what legal protections are important for your business, including patent applications for innovative processes, trademark registration for your brand, and copyright protection for original content. Focus on identifying your proprietary assets, understanding the legal requirements for protection, and developing a strategy to safeguard your competitive advantages."
    
    elif any(keyword in recent_text for keyword in ['product development timeline', 'working prototype', 'mvp', 'milestones', 'launch', 'validate your concept', 'full development']):
        return "Based on your business goals, here's a draft for your product development timeline: Your development timeline should include key milestones such as [prototype development], [MVP creation], [testing and validation], and [full product launch]. Consider what working prototype or MVP you currently have and what milestones you need to reach before launch. Focus on creating a realistic timeline that accounts for development phases, testing periods, and validation steps. Think about how you'll validate your concept before full development and what resources you'll need at each stage."
    
    elif any(keyword in recent_text for keyword in ['mission', 'tagline', 'mission statement', 'business stands for']):
        return "Based on your business vision, here's a draft mission statement: [Business name] aims to [core purpose] by [key approach] to [target outcome]. Consider what your business stands for and how you would describe it in one compelling sentence. Think about your core values, purpose, and what makes you unique. Focus on creating a clear, inspiring statement that guides your business decisions and resonates with your target audience."
    
    elif any(keyword in recent_text for keyword in ['sales', 'projected sales', 'first year', 'sales projections', 'revenue', 'income']):
        return "Based on your business goals, here's a draft for your first-year sales projections: Your projected sales for the first year should be based on realistic market analysis and conservative estimates. Consider factors like your target market size, customer acquisition rate, pricing strategy, and seasonal variations. Focus on creating projections that account for market penetration, customer lifetime value, and repeat business. Think about how you'll reach customers and what conversion rates you can realistically expect based on industry benchmarks and your marketing capabilities."
    
    elif any(keyword in recent_text for keyword in ['startup costs', 'estimated startup costs', 'one-time expenses', 'initial costs', 'launch costs']):
        return "Based on your business needs, here's a draft for your startup costs: Your estimated startup costs should include essential one-time expenses like equipment purchases, initial inventory, legal fees, permits and licenses, website development, initial marketing campaigns, and office setup. Consider both essential startup costs and optional investments that could be deferred to manage cash flow. Focus on creating a comprehensive list of all one-time expenses needed to launch your business, including equipment, technology, legal requirements, and initial marketing. Think about equipment leasing vs. buying, bulk purchasing discounts, and phased implementation to optimize your startup investment."
    
    elif any(keyword in recent_text for keyword in ['financial', 'budget', 'costs', 'expenses', 'funding', 'investment']):
        return "Based on your business requirements, here's a draft for your financial planning: Your financial plan should include startup costs, operating expenses, cash flow projections, and funding requirements. Consider fixed costs (rent, salaries, equipment) and variable costs (materials, marketing, commissions). Focus on creating realistic budgets, identifying funding sources, and planning for financial sustainability. Think about break-even analysis, profit margins, and financial contingency planning to ensure long-term viability."
    
    else:
        return "Based on our conversation, here's a comprehensive draft response that addresses your current question with detailed insights and actionable recommendations tailored to your business context and goals. Consider breaking down complex questions into smaller parts and thinking through each aspect systematically."

def handle_scrapping_command(reply, notes, history, session_data=None):
    """Handle the Scrapping command with actual web search research"""
    print(f"🔍 DEBUG - Scrapping command called with notes: '{notes}'")
    
    # Extract business context from history for targeted research
    business_context = extract_business_context_from_history(history)
    
    # Get current question context for more targeted responses
    current_question = get_current_question_context(history)
    
    # Generate scrapping content based on conversation history and current question
    scrapping_content = generate_scrapping_content(history, business_context, notes, current_question)
    
    scrapping_response = f"Here's a refined version of your thoughts:\n\n{scrapping_content}\n\n"
    
    # If user provided specific research notes, conduct actual web search
    if notes and len(notes.strip()) > 3:
        print(f"🔍 DEBUG - Conducting web search for: '{notes}'")
        scrapping_response += f"**🔍 Researching: {notes}**\n\n"
        scrapping_response += "I'm conducting web search research to provide you with current, actionable insights. This will help refine your approach with real data and trends.\n\n"
        
        # Add verification trigger to show Accept/Modify buttons
        scrapping_response += "**Verification:**\n"
        scrapping_response += "Here's what I've captured so far: "
        
        # Extract key information for verification - use session data if available
        business_name = ""
        if session_data and session_data.get("title"):
            business_name = session_data["title"]
        elif business_context.get("business_name"):
            business_name = business_context["business_name"]
        
        if business_name:
            scrapping_response += f"{business_name} "
        
        # Add complete context from the scrapping response (no truncation)
        scrapping_response += f"with research insights on {notes}. Does this look accurate to you?\n\n"
        
        scrapping_response += "If not, please let me know where you'd like to modify, and we'll work through this some more."
        
        # Add web search trigger for the backend to process
        scrapping_response += f"\n\nWEBSEARCH_QUERY: {notes}"
    else:
        print(f"🔍 DEBUG - No specific research topic, showing usage instructions")
        # If no specific research request, show options
        scrapping_response += "**🔍 Let me research this for you:**\n"
        scrapping_response += "I can conduct web search research to help refine and validate your ideas. This includes:\n"
        scrapping_response += "• **Market Research** - Current trends and opportunities in your field\n"
        scrapping_response += "• **Competitor Analysis** - How others are approaching similar challenges\n"
        scrapping_response += "• **Best Practices** - Proven strategies and successful approaches\n"
        scrapping_response += "• **Industry Insights** - Expert opinions and market data\n\n"
        
        scrapping_response += "**To get started with research, use:**\n"
        scrapping_response += "• **Scrapping: [your research topic]** - I'll research specific topics\n"
        scrapping_response += "• **Scrapping: competitors** - Research your main competitors\n"
        scrapping_response += "• **Scrapping: market trends** - Get current market data\n"
        scrapping_response += "• **Scrapping: best practices** - Find proven strategies\n\n"
        
        scrapping_response += "**Example:** Type 'Scrapping: competitors in AI industry' and I'll conduct comprehensive research for you."
    
    print(f"🔍 DEBUG - Scrapping response generated, length: {len(scrapping_response)}")
    return scrapping_response

def generate_scrapping_content(history, business_context, notes, current_question=""):
    """Generate scrapping content based on conversation history and research notes"""
    # Extract recent user responses to understand what they need research on
    recent_responses = []
    for msg in history[-6:]:  # Look at last 6 messages
        if msg.get('role') == 'user' and msg.get('content'):
            recent_responses.append(msg['content'])
    
    # Use the current_question parameter if provided, otherwise extract from history
    if not current_question:
        current_question = get_current_question_context(history)
    
    # Generate contextual research content based on what they've been discussing
    if not recent_responses:
        return "Based on our conversation, here's a refined analysis that incorporates current market insights and best practices relevant to your business context."
    
    # Look for key topics in recent responses
    recent_text = " ".join(recent_responses).lower()
    
    if any(keyword in recent_text for keyword in ['problem does your business solve', 'who has this problem', 'problem', 'solve', 'pain point', 'need']):
        return "Based on current market research and industry insights, here's a refined analysis of your problem-solution fit: Market research shows evolving customer needs and pain points in your industry. Your solution should leverage emerging opportunities to address unmet needs, innovative approaches to problem-solving, and customer-centric strategies that directly alleviate specific pain points. Focus on validating the problem-solution fit through market research and customer feedback."
    
    elif any(keyword in recent_text for keyword in ['competitor', 'competition', 'market', 'competitive advantage', 'unique value proposition']):
        return "Based on current market research, here's a refined analysis of your competitive landscape: The market shows evolving trends in your industry, with key players focusing on digital transformation and customer experience. Your competitive positioning should leverage emerging opportunities in underserved market segments, innovative technology adoption, and personalized customer engagement strategies."
    
    elif any(keyword in recent_text for keyword in ['location', 'space', 'facility', 'equipment']):
        return "Based on industry best practices and current market conditions, here's a refined approach to your operational requirements: Location strategy should prioritize accessibility, cost efficiency, and scalability. Consider hybrid work models, flexible space arrangements, and technology-enabled operations that can adapt to changing market conditions and customer preferences."
    
    elif any(keyword in recent_text for keyword in ['staff', 'hiring', 'team', 'employee']):
        return "Based on current workforce trends and industry insights, here's a refined approach to your staffing strategy: Focus on building a diverse, skilled team that can adapt to changing market conditions. Consider remote work capabilities, cross-functional skills, and employee retention strategies. Prioritize roles that drive customer value and operational efficiency while building a culture that attracts and retains top talent."
    
    elif any(keyword in recent_text for keyword in ['supplier', 'vendor', 'partner', 'relationship']):
        return "Based on current supply chain trends and partnership best practices, here's a refined approach to your vendor relationships: Build strategic partnerships with suppliers who offer reliability, innovation, and competitive value. Consider diversifying your supplier base, implementing technology-driven vendor management, and developing long-term relationships that support your growth and operational efficiency. Research current market trends in supplier relationships, including digital procurement platforms, sustainable sourcing practices, and risk management strategies. Evaluate potential partners based on their track record, financial stability, and alignment with your business values. Implement vendor management systems to track performance and ensure consistent quality delivery."
    
    elif any(keyword in recent_text for keyword in ['key features and benefits', 'how does it work', 'main components', 'steps involved', 'value or results']):
        return "Based on current market research and industry insights, here's a refined approach to your product features and benefits: Market research shows evolving customer expectations for product functionality, user experience, and measurable outcomes. Your product should leverage emerging technologies, customer-centric design principles, and data-driven approaches to deliver superior value. Focus on clearly articulating the technical capabilities, user journey, and quantifiable benefits that differentiate your solution from competitors."
    
    elif any(keyword in recent_text for keyword in ['intellectual property', 'patents', 'trademarks', 'copyrights', 'proprietary technology', 'unique processes', 'formulas', 'legal protections']):
        return "Based on current intellectual property trends and legal best practices, here's a refined approach to your IP strategy: Market research shows increasing importance of IP protection in competitive markets, with emerging trends in patent filings, trademark enforcement, and trade secret protection. Your IP strategy should leverage current legal frameworks, emerging protection mechanisms, and proactive enforcement strategies. Focus on identifying your proprietary assets, understanding the evolving legal landscape, and developing a comprehensive protection strategy that safeguards your competitive advantages."
    
    elif any(keyword in recent_text for keyword in ['product development timeline', 'working prototype', 'mvp', 'milestones', 'launch', 'validate your concept', 'full development']):
        return "Based on current product development trends and industry insights, here's a refined approach to your development timeline: Market research shows evolving methodologies in product development, with emphasis on agile development, rapid prototyping, and iterative validation. Your development strategy should leverage current best practices in MVP creation, user testing, and market validation. Focus on creating a realistic timeline that incorporates modern development approaches, customer feedback loops, and iterative improvement cycles."
    
    else:
        return "Based on current industry insights and best practices, here's a refined analysis that incorporates market trends, competitive intelligence, and strategic recommendations tailored to your business context and growth objectives."

def handle_support_command(reply, history, session_data=None):
    """Handle the Support command with proactive research assistance"""
    # Extract business context for verification
    business_context = extract_business_context_from_history(history)
    
    # Get current question context for more targeted responses
    current_question = get_current_question_context(history)
    
    # Generate support content based on conversation history and current question
    support_content = generate_support_content(history, business_context, current_question)
    
    support_response = f"Let's work through this together with some deeper context:\n\n{support_content}\n\n"
    
    # Add verification trigger to show Accept/Modify buttons
    support_response += "**Verification:**\n"
    support_response += "Here's what I've captured so far: "
    
    # Extract key information for verification - use session data if available
    business_name = ""
    if session_data and session_data.get("title"):
        business_name = session_data["title"]
    elif business_context.get("business_name"):
        business_name = business_context["business_name"]
    
    if business_name:
        support_response += f"{business_name} "
    
    # Add complete context from the support response (no truncation)
    support_response += f"with insights on {get_question_topic(current_question)}. Does this look accurate to you?\n\n"
    
    support_response += "If not, please let me know where you'd like to modify, and we'll work through this some more."
    
    return support_response

def generate_support_content(history, business_context, current_question=""):
    """Generate support content based on conversation history"""
    # Extract recent messages (both user and assistant) to understand context
    recent_messages = []
    for msg in history[-8:]:  # Look at last 8 messages (4 exchanges)
        if msg.get('content'):
            recent_messages.append(msg['content'])
    
    # Debug logging
    print(f"🔍 DEBUG - Recent messages for support context: {recent_messages}")
    
    # Generate contextual support based on what they've been discussing
    if not recent_messages:
        return "I'm here to provide comprehensive support for your business planning journey. Let me help you think through the current question with additional insights and guidance."
    
    # Look for key topics in recent messages (both questions and responses)
    recent_text = " ".join(recent_messages).lower()
    print(f"🔍 DEBUG - Recent text for analysis: {recent_text[:200]}...")
    
    # Use the current_question parameter if provided, otherwise extract from history
    if not current_question:
        current_question = get_current_question_context(history)
    
    print(f"🔍 DEBUG - Current question context: {current_question[:100]}...")
    
    # Check for specific business plan question topics based on current question
    if any(keyword in current_question for keyword in ['problem does your business solve', 'who has this problem', 'problem', 'solve', 'pain point', 'need']):
        return "Let me help you define your problem-solution fit. Consider what specific problem your business addresses and who experiences this problem. Think about the severity and frequency of this problem, current alternatives available, and why your solution is uniquely positioned to address it. Focus on clearly articulating the problem, identifying your target audience, and explaining how your business provides a superior solution that directly alleviates the pain point."
    
    elif any(keyword in current_question for keyword in ['competitor', 'competition', 'main competitors', 'strengths and weaknesses', 'competitive advantage', 'unique value proposition', 'what makes your business unique']):
        return "Let me help you analyze your competitive landscape. Consider researching your main competitors' strengths and weaknesses, their pricing strategies, and how you can differentiate your offering. Think about what makes your solution unique and how you can position yourself effectively in the market. Focus on identifying 3-5 key competitors and analyzing their market positioning, pricing models, and customer base."
    
    elif any(keyword in current_question for keyword in ['target market', 'demographics', 'psychographics', 'behaviors', 'ideal customer']):
        return "Let me help you define your target market. Consider your ideal customer's demographics (age, income, location), psychographics (interests, values, lifestyle), and behaviors (buying patterns, preferences). Think about how you can reach and connect with this audience effectively. Focus on creating detailed customer personas and understanding their pain points and needs."
    
    elif any(keyword in current_question for keyword in ['location', 'space', 'facility', 'equipment', 'infrastructure', 'where will your business be located']):
        return "Let me help you think through your operational requirements. Consider your space needs, equipment requirements, and how location will impact your business success. Think about accessibility for customers, suppliers, and employees, as well as any special requirements for your industry. Focus on factors like zoning, transportation access, costs, and scalability."
    
    elif any(keyword in current_question for keyword in ['staff', 'hiring', 'team', 'employee', 'operational needs', 'initial staff']):
        return "Let me help you plan your staffing needs. Consider what roles are critical for launch, what skills you need, and how you'll find and retain the right people. Think about your organizational structure and how you'll manage your team effectively. Focus on identifying key positions, required qualifications, and your hiring timeline."
    
    elif any(keyword in current_question for keyword in ['supplier', 'vendor', 'partner', 'relationship', 'key partners']):
        return "Let me help you identify key business relationships. Consider what suppliers and vendors you'll need, how to evaluate them, and how to build strong partnerships. Think about what external resources are critical to your success and how you'll maintain these relationships. Focus on reliability, quality, pricing, and long-term partnership potential. Research potential partners thoroughly, checking their references, financial stability, and capacity to meet your needs. Consider factors like geographic proximity, delivery capabilities, payment terms, and their ability to scale with your business growth. Establish clear communication channels and performance metrics to ensure successful long-term partnerships."
    
    elif any(keyword in current_question for keyword in ['key features and benefits', 'how does it work', 'main components', 'steps involved', 'value or results']):
        return "Let me help you define your key features and benefits. Consider what specific features your product/service offers and what benefits customers will receive. Think about the main components involved and how the process works. Focus on clearly articulating the technical aspects, user experience, and measurable results customers can expect from using your solution."
    
    elif any(keyword in current_question for keyword in ['product', 'service', 'core offering', 'what will you be offering']):
        return "Let me help you define your core product or service. Consider what specific features, benefits, or outcomes customers will receive. Think about how customers will interact with or use your product/service. Focus on your unique value proposition and how you'll deliver exceptional customer experience."
    
    elif any(keyword in current_question for keyword in ['mission', 'tagline', 'mission statement', 'business stands for']):
        return "Let me help you craft your mission statement. Consider what your business stands for and how you would describe it in one compelling sentence. Think about your core values, purpose, and what makes you unique. Focus on creating a clear, inspiring statement that guides your business decisions and resonates with your target audience."
    
    elif any(keyword in current_question for keyword in ['sales', 'projected sales', 'first year', 'sales projections', 'revenue', 'income']):
        return "Let me help you develop realistic sales projections for your first year. Consider your target market size, customer acquisition rate, pricing strategy, and seasonal factors. Think about how you'll reach customers and what conversion rates you can realistically expect. Focus on conservative estimates based on market research, competitor analysis, and your marketing capabilities. Consider factors like customer lifetime value, repeat business, and market penetration rates."
    
    elif any(keyword in current_question for keyword in ['startup costs', 'estimated startup costs', 'one-time expenses', 'initial costs', 'launch costs']):
        return "Let me help you identify and estimate your startup costs. Consider one-time expenses like equipment purchases, initial inventory, legal fees, permits and licenses, website development, initial marketing campaigns, and office setup. Think about both essential startup costs and optional investments that could be deferred. Focus on creating a comprehensive list of all one-time expenses needed to launch your business, including equipment, technology, legal requirements, and initial marketing. Consider factors like equipment leasing vs. buying, bulk purchasing discounts, and phased implementation to manage cash flow."
    
    elif any(keyword in current_question for keyword in ['financial', 'budget', 'costs', 'expenses', 'funding', 'investment']):
        return "Let me help you plan your financial requirements. Consider your startup costs, operating expenses, cash flow needs, and funding requirements. Think about fixed costs (rent, salaries, equipment) and variable costs (materials, marketing, commissions). Focus on creating realistic budgets, identifying funding sources, and planning for financial sustainability. Consider factors like break-even analysis, profit margins, and financial contingency planning."
    
    elif any(keyword in current_question for keyword in ['intellectual property', 'patents', 'trademarks', 'copyrights', 'proprietary technology', 'unique processes', 'formulas', 'legal protections']):
        return "Let me help you understand your intellectual property needs. Consider what unique processes, formulas, or technology your business has that might need legal protection. Think about patents for innovative processes, trademark registration for your brand, and copyright protection for original content. Focus on identifying your proprietary assets, understanding the legal requirements for protection, and developing a strategy to safeguard your competitive advantages."
    
    elif any(keyword in current_question for keyword in ['product development timeline', 'working prototype', 'mvp', 'milestones', 'launch', 'validate your concept', 'full development']):
        return "Let me help you plan your product development timeline. Consider what milestones you need to reach before launch and what working prototype or MVP you currently have. Think about how you'll validate your concept before full development and what resources you'll need at each stage. Focus on creating a realistic timeline that accounts for development phases, testing periods, and validation steps. Consider factors like market validation, technical feasibility, and resource availability when planning your development milestones."
    
    # Fallback to analyzing recent text if current question doesn't match
    elif any(keyword in recent_text for keyword in ['problem does your business solve', 'who has this problem', 'problem', 'solve', 'pain point', 'need']):
        return "Let me help you define your problem-solution fit. Consider what specific problem your business addresses and who experiences this problem. Think about the severity and frequency of this problem, current alternatives available, and why your solution is uniquely positioned to address it. Focus on clearly articulating the problem, identifying your target audience, and explaining how your business provides a superior solution that directly alleviates the pain point."
    
    elif any(keyword in recent_text for keyword in ['competitor', 'competition', 'main competitors', 'strengths and weaknesses', 'competitive advantage', 'unique value proposition', 'what makes your business unique']):
        return "Let me help you analyze your competitive landscape. Consider researching your main competitors' strengths and weaknesses, their pricing strategies, and how you can differentiate your offering. Think about what makes your solution unique and how you can position yourself effectively in the market. Focus on identifying 3-5 key competitors and analyzing their market positioning, pricing models, and customer base."
    
    elif any(keyword in recent_text for keyword in ['target market', 'demographics', 'psychographics', 'behaviors', 'ideal customer']):
        return "Let me help you define your target market. Consider your ideal customer's demographics (age, income, location), psychographics (interests, values, lifestyle), and behaviors (buying patterns, preferences). Think about how you can reach and connect with this audience effectively. Focus on creating detailed customer personas and understanding their pain points and needs."
    
    elif any(keyword in recent_text for keyword in ['location', 'space', 'facility', 'equipment', 'infrastructure', 'where will your business be located']):
        return "Let me help you think through your operational requirements. Consider your space needs, equipment requirements, and how location will impact your business success. Think about accessibility for customers, suppliers, and employees, as well as any special requirements for your industry. Focus on factors like zoning, transportation access, costs, and scalability."
    
    elif any(keyword in recent_text for keyword in ['staff', 'hiring', 'team', 'employee', 'operational needs', 'initial staff']):
        return "Let me help you plan your staffing needs. Consider what roles are critical for launch, what skills you need, and how you'll find and retain the right people. Think about your organizational structure and how you'll manage your team effectively. Focus on identifying key positions, required qualifications, and your hiring timeline."
    
    elif any(keyword in recent_text for keyword in ['supplier', 'vendor', 'partner', 'relationship', 'key partners']):
        return "Let me help you identify key business relationships. Consider what suppliers and vendors you'll need, how to evaluate them, and how to build strong partnerships. Think about what external resources are critical to your success and how you'll maintain these relationships. Focus on reliability, quality, pricing, and long-term partnership potential."
    
    elif any(keyword in recent_text for keyword in ['key features and benefits', 'how does it work', 'main components', 'steps involved', 'value or results']):
        return "Let me help you define your key features and benefits. Consider what specific features your product/service offers and what benefits customers will receive. Think about the main components involved and how the process works. Focus on clearly articulating the technical aspects, user experience, and measurable results customers can expect from using your solution."
    
    elif any(keyword in recent_text for keyword in ['product', 'service', 'core offering', 'what will you be offering']):
        return "Let me help you define your core product or service. Consider what specific features, benefits, or outcomes customers will receive. Think about how customers will interact with or use your product/service. Focus on your unique value proposition and how you'll deliver exceptional customer experience."
    
    elif any(keyword in recent_text for keyword in ['intellectual property', 'patents', 'trademarks', 'copyrights', 'proprietary technology', 'unique processes', 'formulas', 'legal protections']):
        return "Let me help you understand your intellectual property needs. Consider what unique processes, formulas, or technology your business has that might need legal protection. Think about patents for innovative processes, trademark registration for your brand, and copyright protection for original content. Focus on identifying your proprietary assets, understanding the legal requirements for protection, and developing a strategy to safeguard your competitive advantages."
    
    elif any(keyword in recent_text for keyword in ['product development timeline', 'working prototype', 'mvp', 'milestones', 'launch', 'validate your concept', 'full development']):
        return "Let me help you plan your product development timeline. Consider what milestones you need to reach before launch and what working prototype or MVP you currently have. Think about how you'll validate your concept before full development and what resources you'll need at each stage. Focus on creating a realistic timeline that accounts for development phases, testing periods, and validation steps. Consider factors like market validation, technical feasibility, and resource availability when planning your development milestones."
    
    elif any(keyword in recent_text for keyword in ['mission', 'tagline', 'mission statement', 'business stands for']):
        return "Let me help you craft your mission statement. Consider what your business stands for and how you would describe it in one compelling sentence. Think about your core values, purpose, and what makes you unique. Focus on creating a clear, inspiring statement that guides your business decisions and resonates with your target audience."
    
    elif any(keyword in recent_text for keyword in ['sales', 'projected sales', 'first year', 'sales projections', 'revenue', 'income']):
        return "Let me help you develop realistic sales projections for your first year. Consider your target market size, customer acquisition rate, pricing strategy, and seasonal factors. Think about how you'll reach customers and what conversion rates you can realistically expect. Focus on conservative estimates based on market research, competitor analysis, and your marketing capabilities. Consider factors like customer lifetime value, repeat business, and market penetration rates."
    
    elif any(keyword in recent_text for keyword in ['startup costs', 'estimated startup costs', 'one-time expenses', 'initial costs', 'launch costs']):
        return "Let me help you identify and estimate your startup costs. Consider one-time expenses like equipment purchases, initial inventory, legal fees, permits and licenses, website development, initial marketing campaigns, and office setup. Think about both essential startup costs and optional investments that could be deferred. Focus on creating a comprehensive list of all one-time expenses needed to launch your business, including equipment, technology, legal requirements, and initial marketing. Consider factors like equipment leasing vs. buying, bulk purchasing discounts, and phased implementation to manage cash flow."
    
    elif any(keyword in recent_text for keyword in ['financial', 'budget', 'costs', 'expenses', 'funding', 'investment']):
        return "Let me help you plan your financial requirements. Consider your startup costs, operating expenses, cash flow needs, and funding requirements. Think about fixed costs (rent, salaries, equipment) and variable costs (materials, marketing, commissions). Focus on creating realistic budgets, identifying funding sources, and planning for financial sustainability. Consider factors like break-even analysis, profit margins, and financial contingency planning."
    
    else:
        return "I'm here to provide comprehensive support for your business planning journey. Let me help you think through the current question with additional insights, best practices, and strategic guidance to help you make informed decisions. Consider breaking down complex questions into smaller parts and thinking through each aspect systematically."

def handle_draft_more_command(reply, history, session_data=None):
    """Handle the Draft More command to create additional content"""
    # Extract business context for verification
    business_context = extract_business_context_from_history(history)
    
    draft_more_response = f"I'll create additional content for you:\n\n{reply}\n\n"
    
    # Add verification trigger to show Accept/Modify buttons
    draft_more_response += "**Verification:**\n"
    draft_more_response += "Here's what I've captured so far: "
    
    # Extract key information for verification - use session data if available
    business_name = ""
    if session_data and session_data.get("title"):
        business_name = session_data["title"]
    elif business_context.get("business_name"):
        business_name = business_context["business_name"]
    
    if business_name:
        draft_more_response += f"{business_name} "
    
    # Add context from the draft more response
    draft_more_response += f"with additional content on {reply[:80]}... Does this look accurate to you?\n\n"
    
    draft_more_response += "If not, please let me know where you'd like to modify, and we'll work through this some more."
    
    return draft_more_response

def handle_kickstart_command(reply, history, session_data):
    """Handle the Kickstart command"""
    kickstart_response = f"Here are some kickstart resources to get you moving:\n\n{reply}\n\n"
    kickstart_response += "These templates and frameworks are customized for your business context. "
    kickstart_response += "Would you like me to:\n• **Customize** these further for your specific needs\n• **Provide** additional templates or checklists\n• **Move forward** with the current resources"
    
    return kickstart_response

def handle_contact_command(reply, history, session_data):
    """Handle the Who do I contact? command"""
    contact_response = f"Based on your business needs, here are some trusted professionals:\n\n{reply}\n\n"
    contact_response += "These recommendations are tailored to your industry, location, and business stage. "
    contact_response += "Would you like me to:\n• **Research** more specific providers in your area\n• **Provide** contact templates for reaching out\n• **Suggest** questions to ask when interviewing them"
    
    return contact_response

def extract_conversation_context(history):
    """Extract relevant context from conversation history"""
    recent_messages = history[-6:] if len(history) > 6 else history
    context = []
    
    for msg in recent_messages:
        if msg["role"] == "user" and len(msg["content"]) > 10:
            context.append(msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"])
    
    return " | ".join(context)

def extract_business_context_from_history(history):
    """Extract business context information from conversation history"""
    business_context = {
        "business_name": "",
        "industry": "",
        "location": "",
        "business_type": "",
        "target_market": "",
        "business_idea": ""
    }
    
    # Extract from recent messages
    recent_messages = history[-10:] if len(history) > 10 else history
    
    for msg in recent_messages:
        if msg["role"] == "user":
            content = msg["content"].lower()
            
            # Extract business name patterns
            if "business name" in content or "company name" in content:
                # Look for the actual name in the message
                lines = msg["content"].split('\n')
                for line in lines:
                    if ":" in line and len(line.split(':')[1].strip()) > 2:
                        business_context["business_name"] = line.split(':')[1].strip()
                        break
            
            # Extract industry information
            if "industry" in content or "sector" in content:
                lines = msg["content"].split('\n')
                for line in lines:
                    if ":" in line and len(line.split(':')[1].strip()) > 2:
                        business_context["industry"] = line.split(':')[1].strip()
                        break
            
            # Extract location information
            if "location" in content or "city" in content or "state" in content:
                lines = msg["content"].split('\n')
                for line in lines:
                    if ":" in line and len(line.split(':')[1].strip()) > 2:
                        business_context["location"] = line.split(':')[1].strip()
                        break
            
            # Extract business type
            if "business type" in content or "type of business" in content:
                lines = msg["content"].split('\n')
                for line in lines:
                    if ":" in line and len(line.split(':')[1].strip()) > 2:
                        business_context["business_type"] = line.split(':')[1].strip()
                        break
    
    return business_context

async def handle_competitor_research_request(user_input, business_context, history):
    """Handle specific requests for competitor research"""
    
    # Extract business information for targeted research
    industry = business_context.get("industry", "")
    location = business_context.get("location", "")
    business_name = business_context.get("business_name", "")
    business_type = business_context.get("business_type", "")
    
    # Create targeted research queries
    research_queries = []
    
    if industry:
        research_queries.append(f"main competitors in {industry} industry")
        research_queries.append(f"top companies in {industry} market")
        research_queries.append(f"{industry} industry leaders and market share")
    
    if location and industry:
        research_queries.append(f"{industry} companies in {location}")
        research_queries.append(f"local {industry} competitors in {location}")
    
    if business_type:
        research_queries.append(f"{business_type} business competitors")
        research_queries.append(f"successful {business_type} companies")
    
    # Conduct web search for competitor research
    competitor_research_results = []
    
    for query in research_queries[:3]:  # Limit to 3 queries for efficiency
        try:
            search_result = await conduct_web_search(query)
            if search_result and "unable to conduct web research" not in search_result:
                competitor_research_results.append({
                    "query": query,
                    "result": search_result
                })
        except Exception as e:
            print(f"Error conducting competitor research for query '{query}': {e}")
    
    # Generate comprehensive competitor analysis
    if competitor_research_results:
        analysis_prompt = f"""
        Based on the following research results, provide a comprehensive competitor analysis for a business in the {industry} industry:
        
        Business Context:
        - Industry: {industry}
        - Location: {location}
        - Business Type: {business_type}
        - Business Name: {business_name}
        
        Research Results:
        {chr(10).join([f"Query: {r['query']}\nResult: {r['result']}\n" for r in competitor_research_results])}
        
        Please provide:
        1. Main competitors identified
        2. Market positioning analysis
        3. Competitive advantages and weaknesses
        4. Market opportunities
        5. Strategic recommendations
        
        Make this analysis actionable and specific to the business context.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.7,
                max_tokens=1500
            )
            
            return {
                "success": True,
                "analysis": response.choices[0].message.content,
                "research_sources": len(competitor_research_results),
                "queries_used": [r["query"] for r in competitor_research_results]
            }
        except Exception as e:
            print(f"Error generating competitor analysis: {e}")
            return {
                "success": False,
                "error": "Failed to generate competitor analysis",
                "research_sources": len(competitor_research_results)
            }
    else:
        return {
            "success": False,
            "error": "Unable to conduct competitor research at this time",
            "research_sources": 0
        }

async def generate_business_plan_artifact(session_data, conversation_history):
    """Generate comprehensive business plan artifact with deep research"""
    
    # Conduct comprehensive research for business plan
    industry = session_data.get('industry', 'general business')
    location = session_data.get('location', 'United States')
    
    current_year = datetime.now().year
    previous_year = current_year - 1
    
    print(f"🔍 Conducting deep research for {industry} business in {location}")
    
    # Multiple research queries for comprehensive analysis
    market_research = await conduct_web_search(f"market analysis {industry} {location} {previous_year}")
    competitor_research = await conduct_web_search(f"top competitors {industry} business model analysis {previous_year}")
    industry_trends = await conduct_web_search(f"{industry} industry trends opportunities {previous_year}")
    financial_benchmarks = await conduct_web_search(f"{industry} financial benchmarks startup costs {previous_year}")
    
    business_plan_prompt = f"""
    Generate a comprehensive, detailed business plan based on the following conversation history and extensive research:
    
    Session Data: {json.dumps(session_data, indent=2)}
    
    Deep Research Conducted:
    Market Analysis: {market_research}
    Competitor Analysis: {competitor_research}
    Industry Trends: {industry_trends}
    Financial Benchmarks: {financial_benchmarks}
    
    Conversation History: {json.dumps(conversation_history[-20:], indent=2)}
    
    Create a professional business plan that is in-depth, holistic, and highly detailed. This should blend the user's direct answers with research-driven insights to fill in gaps and provide comprehensive coverage of:
    
    1. Executive Summary
    2. Company Description  
    3. Market Analysis (with research-backed insights)
    4. Organization & Management
    5. Product/Service Offering
    6. Marketing & Sales Strategy
    7. Financial Projections
    8. Funding Requirements
    9. Risk Analysis
    10. Implementation Timeline
    
    Include a note at the beginning that this business plan incorporates deep research and market analysis to provide comprehensive insights beyond what was discussed in the questionnaire.
    
    Make this a trust-building milestone that demonstrates deep understanding of both the customer and their business opportunity.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": business_plan_prompt}],
        temperature=0.6
    )
    
    return response.choices[0].message.content

async def generate_roadmap_artifact(session_data, business_plan_data):
    """Generate comprehensive roadmap based on business plan"""
    
    # Research current tools and vendors
    industry = session_data.get('industry', 'general business')
    business_type = session_data.get('business_type', 'startup')
    
    current_year = datetime.now().year
    previous_year = current_year - 1
    
    vendor_research = await conduct_web_search(f"best business tools vendors {industry} {business_type} {previous_year}")
    legal_research = await conduct_web_search(f"business formation requirements {session_data.get('location', 'United States')}")
    
    roadmap_prompt = f"""
    Create a detailed, chronological roadmap for launching this business:
    
    Business Context: {json.dumps(session_data, indent=2)}
    Business Plan Summary: {business_plan_data}
    
    Current Vendor Research: {vendor_research}
    Legal Requirements Research: {legal_research}
    
    Include:
    - Specific timelines and deadlines
    - Clear task ownership (Angel vs User)
    - 3 recommended vendors/platforms per category with current pricing
    - Industry-specific milestones
    - Pre-launch, launch, and post-launch phases
    - Critical path dependencies
    
    Make this actionable and comprehensive for immediate implementation.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": roadmap_prompt}],
        temperature=0.6
    )
    
    return response.choices[0].message.content

async def handle_roadmap_generation(session_data, history):
    """Handle the transition from Plan to Roadmap phase"""
    
    # Generate comprehensive roadmap using RAG principles
    roadmap_content = await generate_detailed_roadmap(session_data, history)
    
    # Create the roadmap presentation message
    roadmap_message = f"""🗺️ **Your Launch Roadmap is Ready!** 🗺️

Congratulations! Based on your comprehensive business plan, I've generated a detailed, actionable launch roadmap that will guide you from planning to execution.

**"The way to get started is to quit talking and begin doing."** – Walt Disney

---

## 📋 **Your Launch Roadmap Overview**

{roadmap_content}

---

## 🎯 **Key Features of Your Roadmap**

✅ **Research-Backed**: Every recommendation is based on current best practices and industry standards
✅ **Actionable Tasks**: Each phase contains specific, executable tasks with clear timelines
✅ **Multiple Options**: Decision points include various options to fit your specific needs
✅ **Local Resources**: Provider recommendations include local service providers where applicable
✅ **Progress Tracking**: Built-in milestones and success metrics for each phase

---

## 🚀 **What's Next**

Your roadmap is now ready for implementation! Each phase is designed to build upon the previous one, ensuring a smooth transition from planning to execution.

**Ready to begin implementation?** Let me know when you're ready to start executing your roadmap, and I'll guide you through each step with detailed instructions, resources, and support.

---

*This roadmap is tailored specifically to your business, industry, and location. Every recommendation is designed to help you build the business of your dreams.*
"""
    
    return {
        "reply": roadmap_message,
        "transition_phase": "ROADMAP_GENERATED",
        "roadmap_content": roadmap_content
    }

async def handle_roadmap_to_implementation_transition(session_data, history):
    """Handle the transition from Roadmap to Implementation phase"""
    
    # Extract business context from session data
    business_name = session_data.get('business_name', 'Your Business')
    industry = session_data.get('industry', 'general business')
    location = session_data.get('location', 'United States')
    
    # Create comprehensive transition message
    transition_message = f"""🚀 **Roadmap to Implementation Transition** 🚀

Congratulations! You've successfully completed your comprehensive business plan and detailed launch roadmap for "{business_name}". Now it's time to transition from planning into execution mode.

**"Success is not final; failure is not fatal: it is the courage to continue that counts."** – Winston Churchill

---

## 🎯 **Time to Transition from Planning to Action**

You've built a solid foundation with your business plan and roadmap. The time has come to transition from planning into execution mode. This is where your entrepreneurial journey truly begins to take shape.

## 🚀 **What's Next: Implementation Phase**

The Implementation phase will guide you through executing each task step-by-step, turning your roadmap into actionable results. Here's what you can expect:

### **Individual Task Guidance**
- Each task presented with detailed descriptions and clear purposes
- Multiple decision options for informed decision-making
- Mentor insights with research-backed guidance tailored to each step

### **Flexible Navigation & Support**
- Tasks presented one at a time with ability to revisit via navigation menu
- Interactive commands: "Help", "Kickstart", and "Who do I contact?"
- Dynamic prompts and inline notifications for real-time feedback

### **Angel's Implementation Assistance**
Throughout implementation, I can help you with:
- Reviewing and drafting contracts and legal documents
- Completing NDAs and other business documentation
- Analysis and research for business decisions
- Creating pitch decks and presentation materials
- Connecting you with local service providers

### **Service Provider Integration**
- Provider tables with credible local service providers for each step
- Local providers clearly marked for your convenience
- Complete with descriptive information and key considerations

### **Progress Tracking**
- Visual progress bars for overall and per-task completion
- Real-time feedback and suggestions as you complete each task
- Completion declaration reminders with documentation uploads

---

## ⚠️ **Important Implementation Notes**

✅ **Research-Backed**: Every recommendation is grounded in deep research and designed to build your dream business
✅ **Real-Time Support**: You'll receive immediate feedback and suggestions as you complete each task
✅ **Documentation**: Remember to declare task completions and upload relevant documentation
✅ **Progress Tracking**: Progress bars will track your completion throughout the implementation phase

---

## 🎉 **Ready to Begin Implementation?**

Your roadmap is complete and ready for execution. The implementation phase will transform your plans into tangible results, guiding you through each step with expert support and local resources.

**Let's start building your business!** When you're ready, I'll guide you through the first implementation task with detailed instructions, multiple options, and all the support you need to succeed.

*This implementation process is tailored specifically to your "{business_name}" business in the {industry} industry, located in {location}. Every recommendation is designed to help you build the business of your dreams.*
"""
    
    return {
        "reply": transition_message,
        "transition_phase": "ROADMAP_TO_IMPLEMENTATION_TRANSITION",
        "roadmap_content": "Ready for implementation transition"
    }

async def generate_detailed_roadmap(session_data, history):
    """Generate detailed roadmap with RAG-powered research"""
    
    # Extract business context from session data and history
    business_name = session_data.get('business_name', 'Your Business')
    industry = session_data.get('industry', 'general business')
    location = session_data.get('location', 'United States')
    business_type = session_data.get('business_type', 'startup')
    
    # Create comprehensive roadmap prompt with RAG research
    roadmap_prompt = f"""
    Generate a comprehensive, research-backed launch roadmap for "{business_name}" - a {business_type} in the {industry} industry located in {location}.
    
    Use the following business context from the completed business plan:
    - Business Name: {business_name}
    - Industry: {industry}
    - Location: {location}
    - Business Type: {business_type}
    
    Create a detailed roadmap with the following phases. IMPORTANT: Format the response as plain text without any markdown formatting, asterisks, or special characters. Use simple headings and bullet points.
    
    Phase 1: Legal Formation & Compliance
    - Business structure selection (LLC, Corporation, Partnership, etc.)
    - Business registration and licensing requirements
    - Tax ID (EIN) application
    - Required permits and licenses
    - Insurance requirements
    - Compliance with local, state, and federal regulations
    
    Phase 2: Financial Planning & Setup
    - Business bank account setup
    - Accounting system implementation
    - Budget planning and cash flow management
    - Funding strategy execution
    - Financial tracking and reporting systems
    - Tax planning and preparation
    
    Phase 3: Product & Operations Development
    - Supply chain setup and vendor relationships
    - Equipment and technology procurement
    - Operational processes and workflows
    - Quality control systems
    - Inventory management
    - Production or service delivery setup
    
    Phase 4: Marketing & Sales Strategy
    - Brand development and positioning
    - Marketing strategy implementation
    - Sales process setup
    - Customer acquisition channels
    - Digital presence (website, social media)
    - Customer relationship management
    
    Phase 5: Full Launch & Scaling
    - Go-to-market strategy execution
    - Team building and hiring
    - Performance monitoring and analytics
    - Growth and scaling strategies
    - Customer feedback and iteration
    - Long-term sustainability planning
    
    For each phase, provide:
    - Specific Tasks: Detailed, actionable steps
    - Timeline: Realistic time estimates
    - Resources Needed: Required tools, services, and expertise
    - Success Metrics: How to measure progress
    - Decision Points: Multiple options where applicable
    - Local Resources: Service providers and resources specific to {location}
    - Potential Challenges: Common obstacles and solutions
    
    Make the roadmap practical, detailed, and tailored to the specific business context. Include specific examples and actionable recommendations.
    
    Format the response as clean, readable text without any markdown syntax, asterisks, or special formatting characters.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": roadmap_prompt}],
            temperature=0.6,
            max_tokens=3000
        )
        
        # Clean any remaining markdown formatting from the response
        roadmap_content = response.choices[0].message.content
        
        # Remove markdown formatting
        import re
        # Remove headers (## **text**)
        roadmap_content = re.sub(r'#{1,6}\s*\*+([^*]+)\*+', r'\1', roadmap_content)
        # Remove bold formatting (**text**)
        roadmap_content = re.sub(r'\*+([^*]+)\*+', r'\1', roadmap_content)
        # Remove horizontal rules (---)
        roadmap_content = re.sub(r'^[-=]{3,}$', '', roadmap_content, flags=re.MULTILINE)
        # Clean up extra whitespace
        roadmap_content = re.sub(r'\n{3,}', '\n\n', roadmap_content)
        
        return roadmap_content.strip()
    except Exception as e:
        print(f"Error generating detailed roadmap: {e}")
        return "Roadmap generation in progress..."