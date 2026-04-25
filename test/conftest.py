"""
Pytest configuration and shared fixtures for RAG pipeline tests
Includes mocks, stubs, and fixtures for testing
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from langchain_core.documents import Document


class MockEmbeddings:
    """Stub embeddings model that returns fixed vectors"""
    def embed_query(self, query: str) -> list:
        return [0.1] * 384

    def embed_documents(self, docs: list) -> list:
        return [[0.1] * 384 for _ in docs]


class MockChatGroq:
    """Stub LLM that returns canned responses"""
    def __init__(self, model_name: str = "test", temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        self.call_count = 0

    def invoke(self, input_data):
        self.call_count += 1
        # Return different responses based on input
        if isinstance(input_data, str):
            text = input_data.lower()
        elif isinstance(input_data, dict):
            text = str(input_data).lower()
        else:
            text = str(input_data).lower()

        if "frequency" in text:
            return "The standard frequency range for Continental Europe is 49.5-50.5 Hz according to NC LFCR standards."
        elif "bdew" in text:
            return "BDEW TAB 2023 covers technical connection requirements for power generation facilities."
        elif "agorameter" in text:
            return "The Agorameter is a platform that provides real-time energy market data and analysis."
        else:
            return "This is a test response from the mock LLM."

    def __call__(self, *args, **kwargs):
        return self


class MockFAISS:
    """Stub FAISS vectorstore that returns mock documents"""
    def __init__(self):
        self.search_count = 0

    def as_retriever(self, search_kwargs=None):
        search_kwargs = search_kwargs or {}
        k = search_kwargs.get("k", 3)

        def retrieve(query):
            self.search_count += 1
            return [
                Document(
                    page_content=f"Mock document {i+1}: Information about {query[:20]}...",
                    metadata={
                        "source": f"doc_{i}.pdf",
                        "page": i+1
                    }
                )
                for i in range(k)
            ]

        return retrieve

    @classmethod
    def load_local(cls, folder_path: str, embeddings, allow_dangerous_deserialization=False):
        return cls()


@pytest.fixture
def mock_embeddings():
    """Fixture providing mock embeddings"""
    return MockEmbeddings()


@pytest.fixture
def mock_llm():
    """Fixture providing mock LLM"""
    return MockChatGroq()


@pytest.fixture
def mock_vectorstore():
    """Fixture providing mock FAISS vectorstore"""
    return MockFAISS()


@pytest.fixture
def project_root_mock(tmp_path):
    """Fixture providing a temporary project root with vectorstore"""
    vectorstore_dir = tmp_path / "data" / "vectorstore"
    vectorstore_dir.mkdir(parents=True)

    # Create a minimal FAISS index structure
    (vectorstore_dir / "index.faiss").write_bytes(b"mock_faiss_data")
    (vectorstore_dir / "index.pkl").write_bytes(b"mock_pkl_data")

    return tmp_path


@pytest.fixture
def mock_config():
    """Fixture providing mock configuration"""
    return {
        "data": {
            "vectorstore_dir": "data/vectorstore"
        },
        "retrieval": {
            "search_kwargs": {
                "k": 3
            }
        },
        "llm": {
            "model_name": "groq/llama-3.1-8b-instant",
            "temperature": 0.7
        },
        "embeddings": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2"
        }
    }


@pytest.fixture
def patch_config(mock_config):
    """Fixture that patches the config globally"""
    with patch("energy_docs_chat.utils.config_loader.config", mock_config):
        with patch("energy_docs_chat.src.chat_with_doc.retrieval.config", mock_config):
            yield mock_config


@pytest.fixture
def patch_models(mock_embeddings, mock_llm):
    """Fixture that patches model loaders"""
    with patch("energy_docs_chat.utils.model_loader.get_embeddings", return_value=mock_embeddings):
        with patch("energy_docs_chat.utils.model_loader.get_llm", return_value=mock_llm):
            with patch("energy_docs_chat.src.chat_with_doc.retrieval.get_embeddings", return_value=mock_embeddings):
                with patch("energy_docs_chat.src.chat_with_doc.retrieval.get_llm", return_value=mock_llm):
                    yield mock_embeddings, mock_llm


@pytest.fixture
def patch_vectorstore(mock_vectorstore):
    """Fixture that patches FAISS loading"""
    with patch("langchain_community.vectorstores.FAISS.load_local", return_value=mock_vectorstore):
        yield mock_vectorstore


@pytest.fixture
def patch_project_root(project_root_mock):
    """Fixture that patches get_project_root"""
    with patch("energy_docs_chat.utils.config_loader.get_project_root", return_value=project_root_mock):
        with patch("energy_docs_chat.src.chat_with_doc.retrieval.get_project_root", return_value=project_root_mock):
            yield project_root_mock


@pytest.fixture
def complete_mocks(patch_config, patch_models, patch_vectorstore, patch_project_root):
    """Fixture that patches everything needed for RetrievalPipeline tests"""
    embeddings, llm = patch_models
    yield {
        "embeddings": embeddings,
        "llm": llm,
        "vectorstore": patch_vectorstore,
        "project_root": patch_project_root
    }
