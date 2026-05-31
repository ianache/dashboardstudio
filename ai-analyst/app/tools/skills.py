import httpx
import yaml
import logging
from typing import Dict, Any
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global skills catalog cache
SKILLS_CATALOG: Dict[str, Any] = {}

async def load_catalog():
    """
    Fetches the skills catalog from the remote URL and updates the global cache.
    """
    global SKILLS_CATALOG
    url = settings.skills_catalog_url
    
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Fetching skills catalog from {url}")
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            catalog_data = yaml.safe_load(response.text)
            if isinstance(catalog_data, dict):
                SKILLS_CATALOG = catalog_data
                logger.info(f"Successfully loaded {len(SKILLS_CATALOG.get('skills', []))} skills from catalog")
            else:
                logger.error("Invalid catalog format: expected a dictionary")
                
    except Exception as e:
        logger.error(f"Failed to load skills catalog: {str(e)}")
        # We don't raise here to allow the service to start even if catalog fails
        # but the execute_skill tool will notice the empty catalog.

async def execute_skill(skill_id: str, parameters: Dict[str, Any] = None) -> str:
    """
    Triggers an operational skill from the platform's catalog.
    
    Use this tool to perform actions like sending emails, updating records, 
    exporting data, or triggering external workflows.
    
    Args:
        skill_id: The unique identifier of the skill to execute (e.g., 'send_email_report', 'notify_slack').
        parameters: A dictionary of key-value pairs required by the specific skill.
    
    Returns:
        A confirmation message indicating if the skill was triggered.
    """
    if not parameters:
        parameters = {}
        
    # In a real implementation, this would call another service (like BFF or Workflow engine)
    # For now, we verify the skill exists in our local catalog and return a mock confirmation.
    
    skills = SKILLS_CATALOG.get("skills", [])
    skill_exists = any(s.get("id") == skill_id for s in skills)
    
    if not skill_exists and SKILLS_CATALOG:
        # If catalog was loaded but skill not found
        return f"Error: Skill '{skill_id}' not found in the catalog."
    
    # Mock successful execution
    return f"Skill {skill_id} triggered successfully with parameters: {parameters}"
