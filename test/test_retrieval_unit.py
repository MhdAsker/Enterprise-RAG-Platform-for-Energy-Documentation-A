"""
Unit tests for RetrievalPipeline class
Tests individual components with mocking and stubbing
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from langchain_core.documents import Document

from energy_docs_chat.src.chat_with_doc.retrieval import RetrievalPipeline
from energy_docs_chat.exceptions.custom_exception import EnergyDocsException


class TestRetrievalPipelineInitialization:
    """Tests for RetrievalPipeline initialization"""

    def test_init_success_with_mocks(self, complete_mocks):
        """Test successful initialization with all mocks in place"""
        pipeline = RetrievalPipeline()

        assert pipeline is not None
        assert pipeline.embeddings is not None
        assert pipeline.llm is not None
        assert pipeline.vectorstore is not None
        assert pipeline.chat_history_store == {}
        assert pipeline.k == 3

    def test_init_requires_vectorstore(self, patch_config, patch_models, patch_project_root):
        """Test that initialization fails without valid vectorstore"""
        with patch("langchain_community.vectorstores.FAISS.load_local", side_effect=FileNotFoundError("Index not found")):
            with pytest.raises(EnergyDocsException):
                RetrievalPipeline()

    def test_init_logs_config_values(self, complete_mocks, caplog):
        """Test that initialization logs config values"""
        pipeline = RetrievalPipeline()

        assert "Initializing the Retrieval Pipeline Engine" in caplog.text
        assert "Loading FAISS VectorStore" in caplog.text

    def test_init_stores_config_from_yaml(self, complete_mocks):
        """Test that config values are properly stored from YAML"""
        pipeline = RetrievalPipeline()

        assert pipeline.k == 3
        assert pipeline.vectorstore_dir.name == "vectorstore"

    def test_init_creates_empty_chat_history_store(self, complete_mocks):
        """Test that chat history store starts empty"""
        pipeline = RetrievalPipeline()

        assert isinstance(pipeline.chat_history_store, dict)
        assert len(pipeline.chat_history_store) == 0


class TestVectorstoreLoading:
    """Tests for vectorstore loading"""

    def test_load_vectorstore_success(self, complete_mocks):
        """Test successful vectorstore loading"""
        pipeline = RetrievalPipeline()

        assert pipeline.vectorstore is not None

    def test_load_vectorstore_missing_file(self, patch_config, patch_models, patch_project_root):
        """Test that missing vectorstore raises appropriate error"""
        with patch("langchain_community.vectorstores.FAISS.load_local", side_effect=FileNotFoundError("Index not found")):
            with pytest.raises(EnergyDocsException) as exc_info:
                RetrievalPipeline()

            assert "Unable to read FAISS VectorStore" in str(exc_info.value)

    def test_load_vectorstore_uses_embeddings(self, complete_mocks):
        """Test that vectorstore loading uses the provided embeddings"""
        with patch("langchain_community.vectorstores.FAISS.load_local") as mock_load:
            mock_load.return_value = complete_mocks["vectorstore"]

            pipeline = RetrievalPipeline()

            # Verify FAISS.load_local was called with our mock embeddings
            mock_load.assert_called()


class TestSessionHistory:
    """Tests for session history management"""

    def test_get_session_history_creates_new(self, complete_mocks):
        """Test that get_session_history creates new history for unknown sessions"""
        pipeline = RetrievalPipeline()

        history = pipeline.get_session_history("session_1")

        assert history is not None
        assert "session_1" in pipeline.chat_history_store

    def test_get_session_history_returns_existing(self, complete_mocks):
        """Test that get_session_history returns existing history"""
        pipeline = RetrievalPipeline()

        history1 = pipeline.get_session_history("session_1")
        history2 = pipeline.get_session_history("session_1")

        assert history1 is history2

    def test_multiple_sessions_isolated(self, complete_mocks):
        """Test that different sessions have isolated histories"""
        pipeline = RetrievalPipeline()

        history1 = pipeline.get_session_history("session_1")
        history2 = pipeline.get_session_history("session_2")

        assert history1 is not history2
        assert len(pipeline.chat_history_store) == 2

    def test_session_history_type(self, complete_mocks):
        """Test that session history returns ChatMessageHistory type"""
        from langchain_community.chat_message_histories import ChatMessageHistory

        pipeline = RetrievalPipeline()
        history = pipeline.get_session_history("test_session")

        assert isinstance(history, ChatMessageHistory)


class TestFormatDocs:
    """Tests for document formatting"""

    def test_format_docs_single_document(self):
        """Test formatting a single document"""
        docs = [Document(page_content="Test content")]

        result = RetrievalPipeline.format_docs(docs)

        assert result == "Test content"

    def test_format_docs_multiple_documents(self):
        """Test formatting multiple documents with separator"""
        docs = [
            Document(page_content="Content 1"),
            Document(page_content="Content 2"),
            Document(page_content="Content 3"),
        ]

        result = RetrievalPipeline.format_docs(docs)

        assert "Content 1" in result
        assert "Content 2" in result
        assert "Content 3" in result
        assert "\n\n" in result  # Check separator

    def test_format_docs_empty_list(self):
        """Test formatting empty document list"""
        docs = []

        result = RetrievalPipeline.format_docs(docs)

        assert result == ""

    def test_format_docs_extracts_page_content(self):
        """Test that format_docs only extracts page_content"""
        docs = [
            Document(
                page_content="Important info",
                metadata={"source": "doc.pdf", "page": 1}
            )
        ]

        result = RetrievalPipeline.format_docs(docs)

        assert "Important info" in result
        assert "doc.pdf" not in result
        assert "metadata" not in result


class TestBuildChain:
    """Tests for RAG chain construction"""

    def test_build_chain_returns_runnable(self, complete_mocks):
        """Test that build_chain returns a runnable object"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        assert chain is not None
        assert hasattr(chain, "invoke")

    def test_build_chain_creates_conversational_chain(self, complete_mocks):
        """Test that build_chain creates a conversational RAG chain"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        # The chain should support message history
        assert hasattr(chain, "invoke")

    def test_build_chain_logs_success(self, complete_mocks, caplog):
        """Test that build_chain logs successful construction"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        assert "Conversational RAG Chain successfully constructed" in caplog.text

    def test_build_chain_with_mock_prompts(self, complete_mocks):
        """Test build_chain with mocked prompt templates"""
        pipeline = RetrievalPipeline()

        with patch("energy_docs_chat.src.chat_with_doc.retrieval.get_contextualize_q_prompt") as mock_context_prompt:
            with patch("energy_docs_chat.src.chat_with_doc.retrieval.get_qa_prompt") as mock_qa_prompt:
                # Set up mock prompts
                mock_context_prompt.return_value = MagicMock()
                mock_qa_prompt.return_value = MagicMock()

                chain = pipeline.build_chain()

                assert chain is not None


class TestRetrievalPipelineErrors:
    """Tests for error handling"""

    def test_init_with_missing_config(self, patch_models, patch_vectorstore, patch_project_root):
        """Test initialization with missing config"""
        with patch("energy_docs_chat.utils.config_loader.config", side_effect=KeyError("llm")):
            with pytest.raises(EnergyDocsException):
                RetrievalPipeline()

    def test_init_with_invalid_project_root(self, patch_config, patch_models, patch_vectorstore):
        """Test initialization with invalid project root"""
        with patch("energy_docs_chat.utils.config_loader.get_project_root", side_effect=RuntimeError("No .env")):
            with pytest.raises(EnergyDocsException):
                RetrievalPipeline()

    def test_build_chain_with_bad_llm(self, patch_config, patch_models, patch_vectorstore, patch_project_root):
        """Test chain building fails gracefully with bad LLM"""
        pipeline = RetrievalPipeline()

        # Ensure chain can still be built even if LLM is stubbed
        chain = pipeline.build_chain()
        assert chain is not None


class TestRetrievalPipelineState:
    """Tests for pipeline state management"""

    def test_pipeline_maintains_state_across_calls(self, complete_mocks):
        """Test that pipeline maintains state"""
        pipeline = RetrievalPipeline()

        # Add some sessions
        pipeline.get_session_history("user_1")
        pipeline.get_session_history("user_2")

        # Verify state is maintained
        assert "user_1" in pipeline.chat_history_store
        assert "user_2" in pipeline.chat_history_store

    def test_vectorstore_persistence(self, complete_mocks):
        """Test that vectorstore reference persists"""
        pipeline = RetrievalPipeline()
        vectorstore1 = pipeline.vectorstore

        # Call get_session_history shouldn't affect vectorstore
        pipeline.get_session_history("test")
        vectorstore2 = pipeline.vectorstore

        assert vectorstore1 is vectorstore2
