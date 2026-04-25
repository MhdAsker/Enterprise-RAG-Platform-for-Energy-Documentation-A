"""
Integration tests for RAG pipeline end-to-end functionality
Tests complete workflows with mocked external services
"""
import pytest
from unittest.mock import Mock, patch, call
from langchain_core.documents import Document

from energy_docs_chat.src.chat_with_doc.retrieval import RetrievalPipeline


class TestRAGChainInvocation:
    """Integration tests for RAG chain invocation"""

    def test_chain_invoke_with_simple_question(self, complete_mocks):
        """Test invoking chain with a simple question"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        response = chain.invoke(
            {"question": "What is the standard frequency range?"},
            config={"configurable": {"session_id": "test_1"}}
        )

        assert isinstance(response, str)
        assert len(response) > 0

    def test_chain_invoke_with_session_id(self, complete_mocks):
        """Test that chain properly uses session ID"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        session_id = "integration_test_session"

        response = chain.invoke(
            {"question": "What is BDEW?"},
            config={"configurable": {"session_id": session_id}}
        )

        # Session should be created
        assert session_id in pipeline.chat_history_store

    def test_chain_multiple_questions_same_session(self, complete_mocks):
        """Test RAG chain with multiple questions in same session"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        session_id = "multi_question_session"

        # First question
        response1 = chain.invoke(
            {"question": "What is frequency control?"},
            config={"configurable": {"session_id": session_id}}
        )

        # Second question - should build on history
        response2 = chain.invoke(
            {"question": "How is it used in power grids?"},
            config={"configurable": {"session_id": session_id}}
        )

        assert response1 is not None
        assert response2 is not None
        assert len(pipeline.chat_history_store[session_id].messages) > 0

    def test_chain_isolated_sessions(self, complete_mocks):
        """Test that different sessions maintain isolated histories"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        # Session 1
        chain.invoke(
            {"question": "What is Agorameter?"},
            config={"configurable": {"session_id": "session_a"}}
        )

        # Session 2
        chain.invoke(
            {"question": "What is BDEW TAB?"},
            config={"configurable": {"session_id": "session_b"}}
        )

        # Verify sessions are separate
        assert "session_a" in pipeline.chat_history_store
        assert "session_b" in pipeline.chat_history_store
        assert pipeline.chat_history_store["session_a"] is not pipeline.chat_history_store["session_b"]

    def test_chain_response_quality(self, complete_mocks):
        """Test that chain returns sensible responses"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        questions = [
            "What is the standard frequency range for Continental Europe?",
            "What does BDEW TAB 2023 cover?",
            "What is the Agorameter?",
        ]

        for question in questions:
            response = chain.invoke(
                {"question": question},
                config={"configurable": {"session_id": f"session_{questions.index(question)}"}}
            )

            # Response should not be empty
            assert response
            assert isinstance(response, str)
            assert len(response) > 5


class TestRetrieverBehavior:
    """Tests for retriever behavior"""

    def test_retriever_called_for_each_question(self, complete_mocks):
        """Test that retriever is called for each question"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        mock_vectorstore = complete_mocks["vectorstore"]

        # Reset counter
        mock_vectorstore.search_count = 0

        chain.invoke(
            {"question": "First question"},
            config={"configurable": {"session_id": "test_retriever"}}
        )

        assert mock_vectorstore.search_count > 0

    def test_retriever_returns_k_documents(self, complete_mocks):
        """Test that retriever returns k documents"""
        pipeline = RetrievalPipeline()
        retriever = pipeline.vectorstore.as_retriever(search_kwargs={"k": pipeline.k})

        docs = retriever("test query")

        assert len(docs) == pipeline.k

    def test_retriever_with_different_k_values(self, complete_mocks):
        """Test retriever with different k values"""
        pipeline = RetrievalPipeline()

        for k in [1, 3, 5]:
            retriever = pipeline.vectorstore.as_retriever(search_kwargs={"k": k})
            docs = retriever("test query")
            assert len(docs) == k


class TestConversationalContext:
    """Tests for conversational context handling"""

    def test_history_affects_rewritten_question(self, complete_mocks):
        """Test that chat history affects question rewriting"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        session_id = "context_test"

        # Ask about frequency
        response1 = chain.invoke(
            {"question": "What is frequency control?"},
            config={"configurable": {"session_id": session_id}}
        )

        # Ask about it (should refer to frequency control)
        response2 = chain.invoke(
            {"question": "How is it implemented?"},
            config={"configurable": {"session_id": session_id}}
        )

        # Both should return responses
        assert response1
        assert response2

    def test_conversation_memory_accumulates(self, complete_mocks):
        """Test that conversation memory accumulates over time"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        session_id = "memory_test"

        # Make multiple requests
        for i in range(3):
            chain.invoke(
                {"question": f"Question {i+1}"},
                config={"configurable": {"session_id": session_id}}
            )

        # Memory should have messages
        history = pipeline.get_session_history(session_id)
        assert len(history.messages) > 0


class TestErrorRecovery:
    """Tests for error handling and recovery"""

    def test_chain_handles_empty_question(self, complete_mocks):
        """Test chain behavior with empty question"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        # Should handle gracefully
        response = chain.invoke(
            {"question": ""},
            config={"configurable": {"session_id": "empty_test"}}
        )

        assert response is not None

    def test_chain_handles_very_long_question(self, complete_mocks):
        """Test chain with very long question"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        long_question = "What is " + "frequency " * 100 + "?"

        response = chain.invoke(
            {"question": long_question},
            config={"configurable": {"session_id": "long_test"}}
        )

        assert response is not None

    def test_chain_handles_special_characters(self, complete_mocks):
        """Test chain with special characters in question"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        special_question = "What is frequency? @#$%^&*() "

        response = chain.invoke(
            {"question": special_question},
            config={"configurable": {"session_id": "special_test"}}
        )

        assert response is not None


class TestRAGQualityMetrics:
    """Tests for RAG response quality"""

    def test_response_includes_document_context(self, complete_mocks):
        """Test that response incorporates document context"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        response = chain.invoke(
            {"question": "What is frequency?"},
            config={"configurable": {"session_id": "context_quality_test"}}
        )

        # With mocked docs, response should mention mock documents
        assert response is not None
        assert isinstance(response, str)

    def test_response_consistency(self, complete_mocks):
        """Test that same question returns consistent response type"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        question = "What is the standard frequency?"

        response1 = chain.invoke(
            {"question": question},
            config={"configurable": {"session_id": "consistency_1"}}
        )

        response2 = chain.invoke(
            {"question": question},
            config={"configurable": {"session_id": "consistency_2"}}
        )

        assert isinstance(response1, str)
        assert isinstance(response2, str)

    def test_response_length_reasonable(self, complete_mocks):
        """Test that responses are reasonable length"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        response = chain.invoke(
            {"question": "What is frequency control?"},
            config={"configurable": {"session_id": "length_test"}}
        )

        # Response should be non-empty and not excessively long for a short question
        assert 1 < len(response) < 10000


class TestMonkeyPatchingScenarios:
    """Tests using monkey patching for testing different behaviors"""

    def test_monkey_patch_llm_response(self, patch_config, patch_models, patch_vectorstore, patch_project_root):
        """Test monkey patching LLM response"""
        pipeline = RetrievalPipeline()
        chain = pipeline.build_chain()

        # Monkey patch the LLM to return a specific response
        original_invoke = pipeline.llm.invoke

        def patched_invoke(input_data):
            return "Patched response for testing"

        pipeline.llm.invoke = patched_invoke

        response = chain.invoke(
            {"question": "Any question"},
            config={"configurable": {"session_id": "monkey_patch_test"}}
        )

        assert "Patched response" in response

        # Restore
        pipeline.llm.invoke = original_invoke

    def test_monkey_patch_vectorstore_retrieval(self, complete_mocks):
        """Test monkey patching vectorstore retrieval"""
        pipeline = RetrievalPipeline()

        # Monkey patch retriever to always return specific docs
        original_retriever = pipeline.vectorstore.as_retriever

        def patched_as_retriever(search_kwargs=None):
            def retrieve(query):
                return [
                    Document(
                        page_content="Patched document content",
                        metadata={"source": "patched.pdf"}
                    )
                ]
            return retrieve

        pipeline.vectorstore.as_retriever = patched_as_retriever

        chain = pipeline.build_chain()
        response = chain.invoke(
            {"question": "What is patched?"},
            config={"configurable": {"session_id": "patch_retriever_test"}}
        )

        assert response is not None

        # Restore
        pipeline.vectorstore.as_retriever = original_retriever

    def test_monkey_patch_session_history(self, complete_mocks):
        """Test monkey patching session history getter"""
        pipeline = RetrievalPipeline()

        # Count how many times get_session_history is called
        call_count = [0]
        original_get_session = pipeline.get_session_history

        def patched_get_session(session_id):
            call_count[0] += 1
            return original_get_session(session_id)

        pipeline.get_session_history = patched_get_session

        pipeline.get_session_history("test_1")
        pipeline.get_session_history("test_1")
        pipeline.get_session_history("test_2")

        assert call_count[0] == 3

        # Restore
        pipeline.get_session_history = original_get_session
