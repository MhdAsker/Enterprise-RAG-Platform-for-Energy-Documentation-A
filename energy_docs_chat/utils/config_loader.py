import os
import sys
import yaml
from pathlib import Path
from energy_docs_chat.logger.custom_logger import logger
from energy_docs_chat.exceptions.custom_exception import EnergyDocsException

from dotenv import load_dotenv

def get_project_root() -> Path:
    """
    Dynamically returns the absolute path to the top-level Project Root (RAG_LLMOPS).
    Use this to safely load files from outside the source code box (like the /data folder).
    """
    # __file__ = config_loader.py -> parent = utils/ -> parent = energy_docs_chat/ -> parent = RAG_LLMOPS/
    return Path(__file__).resolve().parent.parent.parent

def load_config(config_file_name: str = "config.yaml") -> dict:
    """
    Dynamically maps the path back to the config directory, ensuring the script 
    can be run from anywhere in the project root without pathing errors.
    """
    try:
        project_root = get_project_root()
        
        # ⚡ Automatically load the Secret API Keys from .env securely!
        load_dotenv(project_root / ".env")
        
        # Build the exact path to config.yaml (RAG_LLMOPS / energy_docs_chat / config / config.yaml)
        config_path = project_root / "energy_docs_chat" / "config" / config_file_name
        
        logger.info(f"Attempting to load pipeline config from: {config_path}")
        
        # Verify the file is actually there
        if not config_path.exists():
            raise FileNotFoundError(f"Missing crucial configuration file at: {config_path}")
            
        # Safely parse the YAML file
        with open(config_path, "r", encoding="utf-8") as file:
            parsed_config = yaml.safe_load(file)
            
        logger.info("Configuration variables successfully loaded!")
        return parsed_config
        
    except Exception as e:
        # ⚡ Automatically catches the exact line of any YAML syntax or Path errors!
        raise EnergyDocsException(f"Failed to load config file. Error: {str(e)}", sys)

# We initialize this as a Singleton object right here.
# By doing this, we only read from the hard drive ONCE on application start up.
# You can just do `from energy_docs_chat.utils.config_loader import config` anywhere!
config = load_config()
