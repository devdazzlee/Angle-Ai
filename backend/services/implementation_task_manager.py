from openai import AsyncOpenAI
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from services.specialized_agents_service import agents_manager
from services.rag_service import conduct_rag_research, validate_with_rag, generate_rag_insights
from services.service_provider_tables_service import generate_provider_table, get_task_providers

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ImplementationTaskManager:
    """Manages implementation tasks with RAG-powered guidance and service providers"""
    
    def __init__(self):
        self.task_phases = {
            "legal_formation": {
                "name": "Legal Formation & Compliance",
                "tasks": [
                    "business_structure_selection",
                    "business_registration",
                    "tax_id_application",
                    "permits_licenses",
                    "insurance_requirements"
                ]
            },
            "financial_setup": {
                "name": "Financial Planning & Setup",
                "tasks": [
                    "business_bank_account",
                    "accounting_system",
                    "budget_planning",
                    "funding_strategy",
                    "financial_tracking"
                ]
            },
            "operations_development": {
                "name": "Product & Operations Development",
                "tasks": [
                    "supply_chain_setup",
                    "equipment_procurement",
                    "operational_processes",
                    "quality_control",
                    "inventory_management"
                ]
            },
            "marketing_sales": {
                "name": "Marketing & Sales Strategy",
                "tasks": [
                    "brand_development",
                    "marketing_strategy",
                    "sales_process",
                    "customer_acquisition",
                    "digital_presence"
                ]
            },
            "launch_scaling": {
                "name": "Full Launch & Scaling",
                "tasks": [
                    "go_to_market",
                    "team_building",
                    "performance_monitoring",
                    "growth_strategies",
                    "customer_feedback"
                ]
            }
        }
    
    async def get_next_implementation_task(self, session_data: Dict[str, Any], completed_tasks: List[str]) -> Dict[str, Any]:
        """Get the next implementation task based on progress"""
        
        # Determine current phase and next task
        current_phase, next_task_id = self._determine_next_task(completed_tasks)
        
        if not next_task_id:
            return {"status": "completed", "message": "All implementation tasks completed"}
        
        # Generate task details with RAG research
        task_details = await self._generate_task_details(next_task_id, session_data)
        
        # Get service providers for this task
        service_providers = await self._get_task_service_providers(next_task_id, session_data)
        
        # Generate mentor insights
        mentor_insights = await self._generate_mentor_insights(next_task_id, session_data)
        
        return {
            "task_id": next_task_id,
            "phase": current_phase,
            "task_details": task_details,
            "service_providers": service_providers,
            "mentor_insights": mentor_insights,
            "angel_actions": self._get_angel_actions(next_task_id),
            "estimated_time": self._get_estimated_time(next_task_id),
            "priority": self._get_priority(next_task_id)
        }
    
    def _determine_next_task(self, completed_tasks: List[str]) -> tuple[str, str]:
        """Determine the next task based on completed tasks"""
        
        for phase_key, phase_data in self.task_phases.items():
            for task_id in phase_data["tasks"]:
                if task_id not in completed_tasks:
                    return phase_key, task_id
        
        return None, None
    
    async def _generate_task_details(self, task_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed task information using RAG research"""
        
        # Get task name and description
        task_name = task_id.replace('_', ' ').title()
        task_description = f"Complete the {task_name} process for your business"
        
        # Conduct RAG research for this task
        research_query = f"{task_name} business setup {session_data.get('industry', '')} {session_data.get('location', '')}"
        rag_research = await conduct_rag_research(research_query, session_data, "standard")
        
        # Generate task options using AI
        options_prompt = f"""
        Generate 3-4 specific options for completing this business task: {task_name}
        
        Business Context:
        - Industry: {session_data.get('industry', 'General')}
        - Location: {session_data.get('location', 'United States')}
        - Business Type: {session_data.get('business_type', 'Startup')}
        
        Provide practical, actionable options that the user can choose from.
        Format as a list of clear options.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": options_prompt}],
                temperature=0.7,
                max_tokens=300
            )
            options_text = response.choices[0].message.content
            options = [option.strip('- ').strip() for option in options_text.split('\n') if option.strip()]
        except:
            options = [
                "Professional Service Provider",
                "DIY with Online Resources", 
                "Hybrid Approach (Partial DIY + Consultation)",
                "Full Service Package"
            ]
        
        return {
            "title": task_name,
            "description": task_description,
            "purpose": f"Establish proper {task_name.lower()} for business compliance and operations",
            "options": options[:4],  # Limit to 4 options
            "research_insights": rag_research.get('analysis', 'Research insights available'),
            "estimated_time": self._get_estimated_time(task_id),
            "priority": self._get_priority(task_id)
        }
    
    async def _get_task_service_providers(self, task_id: str, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get service providers for a specific task"""
        
        try:
            providers = await get_task_providers(task_id, f"implementation task {task_id}", session_data)
            return providers.get('provider_table', {}).get('providers', [])
        except:
            return []
    
    async def _generate_mentor_insights(self, task_id: str, session_data: Dict[str, Any]) -> str:
        """Generate mentor insights for the task"""
        
        insight_prompt = f"""
        Provide mentor-style insights for this business implementation task: {task_id}
        
        Business Context:
        - Industry: {session_data.get('industry', 'General')}
        - Location: {session_data.get('location', 'United States')}
        - Business Type: {session_data.get('business_type', 'Startup')}
        
        Provide 2-3 key insights that would help a new entrepreneur succeed with this task.
        Include common mistakes to avoid and best practices.
        """
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": insight_prompt}],
                temperature=0.7,
                max_tokens=400
            )
            return response.choices[0].message.content
        except:
            return "Focus on getting this task done right the first time. Take your time to research your options and choose the approach that best fits your business needs and budget."
    
    def _get_angel_actions(self, task_id: str) -> List[str]:
        """Get Angel AI actions for a task"""
        
        action_map = {
            "business_structure_selection": [
                "Generate business structure comparison chart",
                "Research state-specific requirements",
                "Create decision matrix for structure selection"
            ],
            "business_registration": [
                "Draft registration documents",
                "Generate registration checklist",
                "Research filing requirements"
            ],
            "business_bank_account": [
                "Compare bank options and requirements",
                "Generate application documents checklist",
                "Create banking setup timeline"
            ],
            "accounting_system": [
                "Compare accounting software options",
                "Generate chart of accounts template",
                "Create financial tracking procedures"
            ]
        }
        
        return action_map.get(task_id, [
            "Research best practices for this task",
            "Generate implementation checklist",
            "Create timeline and milestones"
        ])
    
    def _get_estimated_time(self, task_id: str) -> str:
        """Get estimated time for task completion"""
        
        time_map = {
            "business_structure_selection": "1-2 days",
            "business_registration": "1-2 weeks", 
            "tax_id_application": "1-3 days",
            "permits_licenses": "2-4 weeks",
            "business_bank_account": "3-5 days",
            "accounting_system": "1 week"
        }
        
        return time_map.get(task_id, "1-2 weeks")
    
    def _get_priority(self, task_id: str) -> str:
        """Get priority level for task"""
        
        high_priority_tasks = [
            "business_structure_selection",
            "business_registration", 
            "tax_id_application",
            "business_bank_account"
        ]
        
        return "High" if task_id in high_priority_tasks else "Medium"