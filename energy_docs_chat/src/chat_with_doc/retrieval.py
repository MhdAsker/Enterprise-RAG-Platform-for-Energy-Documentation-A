import sys
from langchain_community.vectorstores import FAISS
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnablePassthrough, RunnableBranch
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter

# Modular Custom Imports
from energy_docs_chat.utils.config_loader import config, get_project_root
from energy_docs_chat.utils.model_loader import get_llm, get_embeddings
from energy_docs_chat.logger.custom_logger import logger
from energy_docs_chat.exceptions.custom_exception import EnergyDocsException
from energy_docs_chat.prompts.prompts import get_contextualize_q_prompt, get_qa_prompt


class RetrievalPipeline:
    """
    Manages the querying layer of the RAG application by loading the Vector database 
    and bolting it together with our modular Prompt Engine and LLM.
    """
    def __init__(self):
        try:
            logger.info("Initializing the Retrieval Pipeline Engine...")
            
            # 1. Gather configuration parameters safely
            self.project_root = get_project_root()
            self.vectorstore_dir = self.project_root / config["data"]["vectorstore_dir"]
            self.k = config["retrieval"]["search_kwargs"]["k"]
            
            # 2. Load our Modular AI Models
            self.embeddings = get_embeddings()
            self.llm = get_llm()
            
            # 3. Connect to Database and initiate Ephemeral Memory
            self._load_vectorstore()
            self.chat_history_store = {}
            
        except Exception as e:
            raise EnergyDocsException(f"Failed to initialize RetrievalPipeline: {e}", sys)

    def _load_vectorstore(self):
        """Loads the pre-computed FAISS database using the assigned embeddings."""
        try:
            logger.info(f"Loading FAISS VectorStore locally from {self.vectorstore_dir}")
            
            if not self.vectorstore_dir.exists():
                raise FileNotFoundError(
                    f"Index not found at {self.vectorstore_dir}. Did you run data_ingestion.py?"
                )

            self.vectorstore = FAISS.load_local(
                folder_path=str(self.vectorstore_dir),
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True 
            )
            logger.info("VectorStore successfully connected!")
            
        except Exception as e:
            raise EnergyDocsException(f"Unable to read FAISS VectorStore: {e}", sys)

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Helper router to maintain dictionary memory states securely based on Session IDs."""
        if session_id not in self.chat_history_store:
            self.chat_history_store[session_id] = ChatMessageHistory()
        return self.chat_history_store[session_id]

    @staticmethod
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def build_chain(self):
        """
        Constructs our Conversational RAG chain using Pure LCEL (LangChain v1.2+ Standard)
        Stage 1: History Aware Retriever (rewrites "it" into full nouns)
        Stage 2: Question Answering Chain
        """
        try:
            logger.info("Assembling Pure LCEL History-Aware RAG Chain...")
            
            # 1. Base Search Engine
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": self.k})
            
            # 2. Extract Prompts from our prompts.py module
            contextualize_prompt = get_contextualize_q_prompt()
            qa_prompt = get_qa_prompt()
            
            # 3. STAGE 1: Pure LCEL History-Aware Retriever Router
            # If this is the FIRST question (no history), instantly skip the LLM and return the exact string.
            # Otherwise, use the LLM to rewrite the question using chat context.
            has_history = lambda x: len(x.get("chat_history", [])) > 0
            
            history_chain = contextualize_prompt | self.llm | StrOutputParser()
            
            history_aware_retriever = (
                RunnableBranch(
                    (has_history, history_chain),
                    itemgetter("question") # short-circuit!
                )
                | retriever 
                | self.format_docs
            )
            
            # 4. STAGE 2: The Main RAG Generation Chain
            # Safely assigns the retrieved context without losing the original question
            pure_lcel_chain = (
                RunnablePassthrough.assign(
                    context=history_aware_retriever
                )
                | qa_prompt
                | self.llm
                | StrOutputParser()
            )
            
            # 5. Wrap in Memory Dictionary
            conversational_chain = RunnableWithMessageHistory(
                pure_lcel_chain,
                self.get_session_history,
                input_messages_key="question",
                history_messages_key="chat_history"
            )
            
            logger.info("Conversational RAG Chain successfully constructed and ready!")
            return conversational_chain
            
        except Exception as e:
            raise EnergyDocsException(f"Failed to build Conversational Chain: {e}", sys)
