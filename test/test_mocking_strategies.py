"""
Specialized tests demonstrating various mocking strategies
Shows advanced mocking, stubbing, and monkey patching patterns
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call, ANY
from unittest.mock import PropertyMock, call, create_autospec
from contextlib import contextmanager
from pathlib import Path

from energy_docs_chat.src.chat_with_doc.retrieval import RetrievalPipeline


class TestMockingStrategies:
    """Demonstrates different mocking strategies"""

    def test_mock_with_return_value(self, patch_config, patch_models, patch_vectorstore, patch_project_root):
        """Test mocking with simple return value"""
        pipeline = RetrievalPipeline()

        # Direct mock
        mock_method = Mock(return_value="mocked result")
        pipeline.llm.invoke = mock_method

        result = pipeline.llm.invoke({"question": "test"})

        assert result == "mocked result"
        mock_method.assert_called_once()

    def test_mock_with_side_effect(self, patch_config, patch_models, patch_vectorstore, patch_project_root):
        """Test mocking with side effects"""
        pipeline = RetrievalPipeline()

        # Side effect - can raise exceptions or return different values
        def side_effect_func(*args, **kwargs):
            if "error" in str(args):
                raise ValueError("Error in side effect")
            return "success"

        pipeline.llm.invoke = Mock(side_effect=side_effect_func)

        assert pipeline.llm.invoke({"question": "normal"}) == "success"

        with pytest.raises(ValueError):
            pipeline.llm.invoke({"question": "error"})

    def test_mock_call_assertions(self, patch_config, patch_models, patch_vectorstore, patch_project_root):
        """Test asserting mock was called correctly"""
        pipeline = RetrievalPipeline()

        pipeline.llm.invoke = Mock(return_value="result")

        # Call the mock
        pipeline.llm.invoke({"question": "test"})

        # Assert it was called
        pipeline.llm.invoke.assert_called_once()
        pipeline.llm.invoke.assert_called_with({"question": "test"})
        assert pipeline.llm.invoke.call_count == 1

    def test_mock_multiple_calls(self, patch_config, patch_models, patch_vectorstore, patch_project_root):
        """Test mocking with multiple calls"""
        pipeline = RetrievalPipeline()

        pipeline.llm.invoke = Mock(return_value="result")

        # Call multiple times
        pipeline.llm.invoke("first")
        pipeline.llm.invoke("second")
        pipeline.llm.invoke("third")

        # Assert all calls
        assert pipeline.llm.invoke.call_count == 3
        pipeline.llm.invoke.assert_has_calls([
            call("first"),
            call("second"),
            call("third")
        ])

    def test_autospec_mock(self, patch_config, patch_models, patch_vectorstore, patch_project_root):
        """Test creating autospec mock (follows original signature)"""
        pipeline = RetrievalPipeline()

        # Create autospec that follows ChatMessageHistory interface
        from langchain_community.chat_message_histories import ChatMessageHistory

        mock_history = create_autospec(ChatMessageHistory, instance=True)
        mock_history.add_message = Mock()

        # Add message should work like the real one
        mock_history.add_message("test message")
        mock_history.add_message.assert_called_with("test message")


class TestStubbingStrategies:
    """Demonstrates stubbing (providing minimal implementations)"""

    def test_stub_minimal_llm(self, patch_config, patch_models, patch_vectorstore, patch_project_root):
        """Test stubbing with minimal implementation"""
        pipeline = RetrievalPipeline()

        # Stub with minimal implementation
        class MinimalLLMStub:
            def invoke(self, input_data):
                return "stub response"

        pipeline.llm = MinimalLLMStub()

        result = pipeline.llm.invoke({"question": "test"})
        assert result == "stub response"

    def test_stub_with_behavior(self, patch_config, patch_models, patch_vectorstore, patch_project_root):
        """Test stub with some behavior"""
        pipeline = RetrievalPipeline()

        class SmartStub:
            def invoke(self, input_data):
                question = input_data.get("question", "")
                if "frequency" in question.lower():
                    return "Frequency information"
                elif "bdew" in question.lower():
                    return "BDEW information"
                return "Generic response"

        pipeline.llm = SmartStub()

        assert "Frequency" in pipeline.llm.invoke({"question": "What about frequency?"})
        assert "BDEW" in pipeline.llm.invoke({"question": "What is BDEW?"})
        assert "Generic" in pipeline.llm.invoke({"question": "Random question"})

    def test_stub_with_state(self, patch_config, patch_models, patch_vectorstore, patch_project_root):
        """Test stub that maintains state"""
        pipeline = RetrievalPipeline()

        class StatefulStub:
            def __init__(self):
                self.call_count = 0
                self.calls = []

            def invoke(self, input_data):
                self.call_count += 1
                self.calls.append(input_data)
                return f"Response {self.call_count}"

        stub = StatefulStub()
        pipeline.llm = stub

        # Make multiple calls
        result1 = pipeline.llm.invoke({"question": "Q1"})
        result2 = pipeline.llm.invoke({"question": "Q2"})

        assert result1 == "Response 1"
        assert result2 == "Response 2"
        assert len(stub.calls) == 2


class TestMonkeyPatchingStrategies:
    """Demonstrates monkey patching (runtime behavior modification)"""

    def test_monkey_patch_function(self, complete_mocks):
        """Test basic monkey patching of a function"""
        pipeline = RetrievalPipeline()

        # Store original
        original_format = RetrievalPipeline.format_docs

        # Monkey patch
        RetrievalPipeline.format_docs = staticmethod(lambda docs: "PATCHED: " + original_format(docs))

        from langchain_core.documents import Document
        docs = [Document(page_content="test")]

        result = pipeline.format_docs(docs)

        assert "PATCHED:" in result

        # Restore
        RetrievalPipeline.format_docs = original_format

    def test_monkey_patch_instance_method(self, complete_mocks):
        """Test monkey patching instance methods"""
        pipeline = RetrievalPipeline()

        # Store original
        original_get_history = pipeline.get_session_history

        # Monkey patch
        call_log = []

        def patched_get_history(session_id):
            call_log.append(session_id)
            return original_get_history(session_id)

        pipeline.get_session_history = patched_get_history

        # Use it
        pipeline.get_session_history("session_1")
        pipeline.get_session_history("session_2")

        assert call_log == ["session_1", "session_2"]

        # Restore
        pipeline.get_session_history = original_get_history

    def test_monkey_patch_attribute(self, complete_mocks):
        """Test monkey patching attributes"""
        pipeline = RetrievalPipeline()

        # Store original
        original_k = pipeline.k

        # Monkey patch
        pipeline.k = 10

        assert pipeline.k == 10

        # Restore
        pipeline.k = original_k
        assert pipeline.k == original_k

    def test_monkey_patch_with_context_manager(self, complete_mocks):
        """Test monkey patching with context manager"""
        pipeline = RetrievalPipeline()

        original_k = pipeline.k

        @contextmanager
        def patch_k(new_value):
            nonlocal pipeline
            old_value = pipeline.k
            pipeline.k = new_value
            try:
                yield
            finally:
                pipeline.k = old_value

        # Use patching
        with patch_k(20):
            assert pipeline.k == 20

        # Should be restored
        assert pipeline.k == original_k


class TestPartialMocking:
    """Tests combining multiple mocking strategies"""

    def test_mock_and_stub_together(self, patch_config, patch_models, patch_vectorstore, patch_project_root):
        """Test using both mocks and stubs together"""
        pipeline = RetrievalPipeline()

        # Stub embeddings
        class EmbeddingsStub:
            def embed_query(self, q):
                return [0.1] * 384

        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value="mocked response")

        pipeline.embeddings = EmbeddingsStub()
        pipeline.llm = mock_llm

        # Test
        embedding = pipeline.embeddings.embed_query("test")
        response = pipeline.llm.invoke({"question": "test"})

        assert len(embedding) == 384
        assert response == "mocked response"
        mock_llm.invoke.assert_called_once()

    def test_selective_patching(self, complete_mocks):
        """Test patching only specific methods"""
        pipeline = RetrievalPipeline()

        # Patch only specific methods
        with patch.object(pipeline, "get_session_history", return_value=Mock()):
            history = pipeline.get_session_history("test")
            assert history is not None

        # Original behavior should work after context
        history2 = pipeline.get_session_history("test2")
        assert history2 is not None


class TestPropertyMocking:
    """Tests for mocking properties and attributes"""

    def test_mock_property(self, complete_mocks):
        """Test mocking properties with PropertyMock"""
        pipeline = RetrievalPipeline()

        with patch.object(
            RetrievalPipeline,
            "k",
            new_callable=PropertyMock
        ) as mock_k:
            mock_k.return_value = 999

            assert pipeline.k == 999


class TestCallableObjectMocking:
    """Tests for mocking callable objects and lambdas"""

    def test_mock_retriever_callable(self, complete_mocks):
        """Test mocking retriever (which is a callable)"""
        pipeline = RetrievalPipeline()

        # Create mock retriever
        mock_retriever = Mock(return_value=[])

        # Replace with mock
        original_as_retriever = pipeline.vectorstore.as_retriever
        pipeline.vectorstore.as_retriever = Mock(return_value=mock_retriever)

        retriever = pipeline.vectorstore.as_retriever()
        results = retriever("test query")

        assert results == []
        mock_retriever.assert_called_once_with("test query")


class TestContextManagerMocking:
    """Tests for mocking context managers"""

    def test_mock_context_manager(self, complete_mocks):
        """Test mocking a context manager"""
        mock_cm = MagicMock()
        mock_cm.__enter__ = Mock(return_value="entered")
        mock_cm.__exit__ = Mock(return_value=False)

        with mock_cm as value:
            assert value == "entered"

        mock_cm.__enter__.assert_called_once()
        mock_cm.__exit__.assert_called_once()
