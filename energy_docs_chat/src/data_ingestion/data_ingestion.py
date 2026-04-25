import sys
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# Project-specific imports
from energy_docs_chat.utils.config_loader import config, get_project_root
from energy_docs_chat.utils.model_loader import get_embeddings
from energy_docs_chat.logger.custom_logger import logger
from energy_docs_chat.exceptions.custom_exception import EnergyDocsException

class DataIngestion:
    """
    Handles the entire Extraction, Transformation, and Loading (ETL) pipeline
    for your Energy PDFs into the FAISS Vector Database.
    """
    def __init__(self):
        try:
            # Safely resolve absolute paths directly from our configuration helper
            self.project_root = get_project_root()
            self.docs_dir = self.project_root / config["data"]["docs_dir"]
            self.vectorstore_dir = self.project_root / config["data"]["vectorstore_dir"]
            
            # Extract text splitting dimensions
            self.chunk_size = config["text_splitter"]["chunk_size"]
            self.chunk_overlap = config["text_splitter"]["chunk_overlap"]
            
            # Instantiate the HuggingFace Embeddings globally for the class
            self.embeddings = get_embeddings()
            
        except Exception as e:
            raise EnergyDocsException(f"Failed to initialize DataIngestion configurations: {e}", sys)


    def load_documents(self) -> List[Document]:
        """Loads PDFs identically to how we evaluated them in the notebook."""
        try:
            logger.info(f"Loading PDFs from directory: {self.docs_dir}")
            
            loader = PyPDFDirectoryLoader(str(self.docs_dir))
            documents = loader.load()
            
            logger.info(f"Successfully loaded {len(documents)} document pages.")
            return documents
        except Exception as e:
            raise EnergyDocsException(f"Failed during PyPDF document loading: {e}", sys)


    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Chunks the documents to ensure context sizes stay within LLM limits."""
        try:
            logger.info(f"Applying text splitter (Size: {self.chunk_size}, Overlap: {self.chunk_overlap})")
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                add_start_index=True 
            )
            
            chunks = text_splitter.split_documents(documents)
            
            logger.info(f"Split completed: Produced {len(chunks)} contextual chunks.")
            return chunks
        except Exception as e:
            raise EnergyDocsException(f"Failed during RecursiveCharacter text splitting: {e}", sys)


    def create_and_save_vectorstore(self, chunks: List[Document]):
        """Generates embeddings and saves them to a structured FAISS index."""
        try:
            logger.info("Building FAISS Vector Database... (This may take a minute natively)")
            
            vectorstore = FAISS.from_documents(chunks, self.embeddings)
            logger.info(f"FAISS database constructed with {vectorstore.index.ntotal} vectors!")
            
            # Save to disk using our configured path
            vectorstore.save_local(str(self.vectorstore_dir))
            logger.info(f"Successfully saved FAISS index to disk at: {self.vectorstore_dir}")
            
            return vectorstore
        except Exception as e:
            raise EnergyDocsException(f"Failed while embedding or saving FAISS store: {e}", sys)
        

    def run_pipeline(self):
        """End-to-End executor for the ingestion phase."""
        try:
            logger.info("========== Starting Data Ingestion Pipeline ==========")
            
            docs = self.load_documents()
            chunks = self.split_documents(docs)
            vectorstore = self.create_and_save_vectorstore(chunks)
            
            logger.info("========== Data Ingestion Pipeline Completed! ==========")
            return vectorstore
        except Exception as e:
            raise EnergyDocsException(f"Pipeline crashed during execution: {e}", sys)

if __name__ == "__main__":
    # This allows you to test the pipeline by simply running: 
    # 'python data_ingestion.py' from your terminal!
    pipeline = DataIngestion()
    pipeline.run_pipeline()
