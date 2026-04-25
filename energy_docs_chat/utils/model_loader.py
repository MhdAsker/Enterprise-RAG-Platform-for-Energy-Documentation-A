import sys
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

# Local imports
from energy_docs_chat.utils.config_loader import config
from energy_docs_chat.logger.custom_logger import logger
from energy_docs_chat.exceptions.custom_exception import EnergyDocsException

def get_llm() -> ChatGroq:
    """
    Dynamically initializes the selected primary Language Model based on config.yaml.
    """
    try:
        model_name = config["llm"]["model_name"]
        temperature = config["llm"]["temperature"]
        
        logger.info(f"Loading Primary LLM: {model_name} with temperature {temperature}")
        
        # Initialize Groq (automatically parses GROQ_API_KEY from the environment)
        llm = ChatGroq(
            model_name=model_name, 
            temperature=temperature
        )
        return llm
        
    except Exception as e:
        raise EnergyDocsException(f"Failed to initialize Language Model: {str(e)}", sys)


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Dynamically initializes the local Embedding model based on config.yaml.
    """
    try:
        model_name = config["embeddings"]["model_name"]
        
        logger.info(f"Loading Embedding Model: {model_name}")
        
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name
        )
        return embeddings
        
    except Exception as e:
        raise EnergyDocsException(f"Failed to initialize Embedding Model: {str(e)}", sys)

