# v3.0.1 - Work Package 1: Role Manager (Updated Default Model)
import os
import glob
from typing import List, Optional
from models import AgentConfig

class RoleManager:
    """
    Manages loading and parsing of agent role templates from the filesystem.
    """
    def __init__(self, roles_dir: str = "roles"):
        self.roles_dir = roles_dir
        self._ensure_roles_dir()

    def _ensure_roles_dir(self):
        if not os.path.exists(self.roles_dir):
            try:
                os.makedirs(self.roles_dir)
            except OSError as e:
                print(f"[RoleManager] Error creating directory {self.roles_dir}: {e}")

    def list_available_roles(self) -> List[str]:
        try:
            pattern = os.path.join(self.roles_dir, "*.txt")
            files = glob.glob(pattern)
            return [os.path.splitext(os.path.basename(f))[0] for f in files]
        except Exception as e:
            print(f"[RoleManager] Error listing roles: {e}")
            return []

    # UPDATED DEFAULT ARGUMENT
    def load_role(self, role_id: str, default_model: str = "google/gemini-2.5-flash-lite") -> Optional[AgentConfig]:
        filepath = os.path.join(self.roles_dir, f"{role_id}.txt")
        
        if not os.path.exists(filepath):
            print(f"[RoleManager] Role file not found: {filepath}")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            name = role_id.capitalize()
            system_prompt = content
            
            lines = content.split('\n')
            if lines and lines[0].lower().startswith("name:"):
                name = lines[0].split(':', 1)[1].strip()
                system_prompt = '\n'.join(lines[1:]).strip()

            return AgentConfig(
                id=role_id,
                name=name,
                system_prompt=system_prompt,
                model_name=default_model,
                temperature=0.7
            )
        except Exception as e:
            print(f"[RoleManager] Error loading role {role_id}: {e}")
            return None
