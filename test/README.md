# RAG Pipeline Test Suite

Comprehensive testing framework for the Energy Docs RAG system with unit tests, integration tests, and advanced mocking strategies.

## Overview

- **~500 test cases** across 4 test modules
- **Advanced mocking**: Stubs, monkey patching, autospec, context managers
- **Unit tests**: RetrievalPipeline components in isolation
- **Integration tests**: Full RAG chain workflows with mocked external services
- **API tests**: FastAPI endpoints with comprehensive coverage

## Test Modules

### 1. `conftest.py` - Fixtures & Mocks
Shared pytest fixtures and mock objects used across all tests.

**Key Components:**
- `MockEmbeddings`: Stub embeddings model (fixed 384-dim vectors)
- `MockChatGroq`: Stub LLM with context-aware responses
- `MockFAISS`: Stub FAISS vectorstore with document retrieval
- Fixtures: `mock_embeddings`, `mock_llm`, `mock_vectorstore`, `complete_mocks`, etc.

**Example Usage:**
```python
def test_something(complete_mocks):
    pipeline = RetrievalPipeline()
    # Everything is mocked and ready
```

### 2. `test_retrieval_unit.py` - Unit Tests (120+ tests)
Tests for individual RetrievalPipeline components.

**Test Classes:**
- `TestRetrievalPipelineInitialization`: Init, config loading, error handling
- `TestVectorstoreLoading`: FAISS loading, error cases
- `TestSessionHistory`: Session management, isolation
- `TestFormatDocs`: Document formatting utilities
- `TestBuildChain`: RAG chain construction
- `TestRetrievalPipelineErrors`: Error handling paths
- `TestRetrievalPipelineState`: State persistence

**Key Tests:**
```python
# Test initialization with mocks
def test_init_success_with_mocks(complete_mocks):
    pipeline = RetrievalPipeline()
    assert pipeline.k == 3

# Test session isolation
def test_multiple_sessions_isolated(complete_mocks):
    pipeline = RetrievalPipeline()
    h1 = pipeline.get_session_history("s1")
    h2 = pipeline.get_session_history("s2")
    assert h1 is not h2

# Test error handling
def test_init_requires_vectorstore(patch_config, patch_models):
    with patch("langchain_community.vectorstores.FAISS.load_local", 
               side_effect=FileNotFoundError()):
        with pytest.raises(EnergyDocsException):
            RetrievalPipeline()
```

### 3. `test_retrieval_integration.py` - Integration Tests (80+ tests)
End-to-end tests of the complete RAG chain.

**Test Classes:**
- `TestRAGChainInvocation`: Full chain invocation, multi-turn conversations
- `TestRetrieverBehavior`: Retriever functionality, document retrieval
- `TestConversationalContext`: History-aware behavior
- `TestErrorRecovery`: Error handling in full chain
- `TestRAGQualityMetrics`: Response quality checks
- `TestMonkeyPatchingScenarios`: Advanced monkey patching patterns

**Key Tests:**
```python
# Test full chain invocation
def test_chain_invoke_with_simple_question(complete_mocks):
    pipeline = RetrievalPipeline()
    chain = pipeline.build_chain()
    response = chain.invoke(
        {"question": "What is frequency?"},
        config={"configurable": {"session_id": "test"}}
    )
    assert isinstance(response, str)

# Test conversation memory
def test_conversation_memory_accumulates(complete_mocks):
    # Make 3 requests to same session
    # Verify history accumulates

# Test monkey patching LLM
def test_monkey_patch_llm_response(complete_mocks):
    pipeline = RetrievalPipeline()
    original = pipeline.llm.invoke
    
    # Patch to return fixed response
    pipeline.llm.invoke = lambda x: "Patched response"
    
    response = chain.invoke({"question": "Test"}, ...)
    assert "Patched response" in response
    
    # Restore
    pipeline.llm.invoke = original
```

### 4. `test_api_endpoints.py` - API Tests (100+ tests)
FastAPI endpoint testing with request/response validation.

**Test Classes:**
- `TestHealthEndpoint`: Health check endpoint tests
- `TestWebUIEndpoint`: HTML UI serving
- `TestChatEndpoint`: Chat API endpoint validation
- `TestStaticFiles`: Static file serving
- `TestAPIDocumentation`: Swagger, ReDoc, OpenAPI tests
- `TestErrorHandling`: Error response codes and messages
- `TestResponseModels`: Pydantic model validation
- `TestConcurrentRequests`: Multiple simultaneous requests

**Key Tests:**
```python
# Test chat endpoint
def test_chat_returns_200_with_valid_request(client, mock_rag_chain):
    with patch("main.rag_chain", mock_rag_chain):
        response = client.post(
            "/chat",
            json={"question": "Test", "session_id": "test"}
        )
        assert response.status_code == 200

# Test response structure
def test_chat_returns_correct_structure(client, mock_rag_chain):
    response = client.post("/chat", json={...})
    data = response.json()
    assert all(k in data for k in ["question", "answer", "session_id", "timestamp"])

# Test error handling
def test_chat_missing_question_returns_422(client):
    response = client.post("/chat", json={"session_id": "test"})
    assert response.status_code == 422
```

### 5. `test_mocking_strategies.py` - Mocking Demo Tests (70+ tests)
Advanced mocking patterns and demonstrations.

**Test Classes:**
- `TestMockingStrategies`: Mock basics, return values, side effects, assertions
- `TestStubbingStrategies`: Minimal implementations, stateful stubs
- `TestMonkeyPatchingStrategies`: Runtime behavior modification
- `TestPartialMocking`: Combining multiple strategies
- `TestPropertyMocking`: Property and attribute mocking
- `TestCallableObjectMocking`: Mocking callables and retrievers
- `TestContextManagerMocking`: Context manager mocking

**Key Examples:**
```python
# Mock with return value
pipeline.llm.invoke = Mock(return_value="mocked")

# Mock with side effect
pipeline.llm.invoke = Mock(side_effect=lambda x: "response")

# Stub with behavior
class SmartStub:
    def invoke(self, input_data):
        if "frequency" in input_data.get("question", ""):
            return "Frequency info"
        return "Generic"

# Monkey patch instance method
original = pipeline.get_session_history
def patched(session_id):
    print(f"Called with {session_id}")
    return original(session_id)
pipeline.get_session_history = patched

# Monkey patch with context manager
@contextmanager
def patch_k(value):
    old = pipeline.k
    pipeline.k = value
    try:
        yield
    finally:
        pipeline.k = old
```

## Running Tests

### Install Test Dependencies
```bash
uv pip install pytest pytest-asyncio pytest-timeout pytest-cov
```

### Run All Tests
```bash
uv run pytest test/
```

### Run Specific Test Module
```bash
uv run pytest test/test_retrieval_unit.py
uv run pytest test/test_api_endpoints.py
```

### Run Specific Test Class
```bash
uv run pytest test/test_retrieval_unit.py::TestRetrievalPipelineInitialization
```

### Run Specific Test
```bash
uv run pytest test/test_retrieval_unit.py::TestRetrievalPipelineInitialization::test_init_success_with_mocks
```

### Run with Verbose Output
```bash
uv run pytest test/ -v
```

### Run with Coverage Report
```bash
uv run pytest test/ --cov=energy_docs_chat --cov-report=html
```

### Run Only Integration Tests
```bash
uv run pytest test/test_retrieval_integration.py
```

### Run with Markers
```bash
uv run pytest test/ -m "unit"     # Unit tests only
uv run pytest test/ -m "integration"  # Integration tests
```

## Mocking Strategies Used

### 1. **Mock Objects** (`unittest.mock.Mock`)
Simple replacements with configurable return values and assertions.
```python
mock_llm = Mock(return_value="response")
mock_llm.assert_called_once_with({"question": "test"})
```

### 2. **Stubs**
Minimal implementations that replace real components.
```python
class MockEmbeddings:
    def embed_query(self, q):
        return [0.1] * 384
```

### 3. **Monkey Patching**
Runtime replacement of methods, attributes, and functions.
```python
original = pipeline.llm.invoke
pipeline.llm.invoke = lambda x: "patched"
# ... test ...
pipeline.llm.invoke = original
```

### 4. **Patch Decorators**
Using `@patch` decorator for clean test isolation.
```python
@patch("energy_docs_chat.utils.model_loader.get_llm")
def test_something(mock_get_llm):
    mock_get_llm.return_value = mock_llm
```

### 5. **Fixtures**
Pytest fixtures for reusable test setup.
```python
@pytest.fixture
def complete_mocks(patch_config, patch_models, patch_vectorstore):
    yield {"embeddings": ..., "llm": ..., ...}
```

### 6. **Side Effects**
Making mocks behave differently based on input.
```python
mock_llm.invoke = Mock(
    side_effect=lambda x: "freq" if "frequency" in str(x) else "other"
)
```

### 7. **AutoSpec**
Creating mocks that enforce the original interface.
```python
mock = create_autospec(RetrievalPipeline, instance=True)
```

## Test Coverage Goals

| Module | Target | Current |
|--------|--------|---------|
| retrieval.py | >90% | Unit + Integration |
| main.py (API) | >85% | API tests |
| Overall | >85% | Across all modules |

## Key Test Patterns

### 1. Isolation
Each test uses complete mocking to isolate the component being tested.

### 2. No Real API Calls
All Groq API and HuggingFace calls are mocked - tests run without GROQ_API_KEY.

### 3. State Verification
Tests verify both immediate returns AND side effects (state changes).

### 4. Error Paths
Every error case is explicitly tested with appropriate exception assertions.

### 5. Edge Cases
Tests cover empty inputs, very long inputs, special characters, etc.

## Example Test Patterns

### Testing Initialization with Mocks
```python
def test_init_with_full_mocks(complete_mocks):
    # All dependencies are already patched via fixtures
    pipeline = RetrievalPipeline()
    assert pipeline.vectorstore is not None
    assert pipeline.llm is not None
```

### Testing Error Handling
```python
def test_init_fails_without_vectorstore(patch_config, patch_models):
    with patch("langchain_community.vectorstores.FAISS.load_local", 
               side_effect=FileNotFoundError()):
        with pytest.raises(EnergyDocsException):
            RetrievalPipeline()
```

### Testing Full Workflow
```python
def test_multi_turn_conversation(complete_mocks):
    pipeline = RetrievalPipeline()
    chain = pipeline.build_chain()
    
    # Turn 1
    r1 = chain.invoke({"question": "What is frequency?"}, 
                      config={"configurable": {"session_id": "s1"}})
    
    # Turn 2 - builds on history
    r2 = chain.invoke({"question": "How is it measured?"},
                      config={"configurable": {"session_id": "s1"}})
    
    assert r1 and r2
    assert len(pipeline.get_session_history("s1").messages) > 0
```

### Monkey Patching for Testing
```python
def test_with_monkey_patch(complete_mocks):
    pipeline = RetrievalPipeline()
    
    # Temporarily replace behavior
    original = pipeline.llm.invoke
    pipeline.llm.invoke = lambda x: "test response"
    
    # Test behavior
    response = pipeline.llm.invoke({})
    assert response == "test response"
    
    # Restore original
    pipeline.llm.invoke = original
```

## Troubleshooting

### Tests Fail with "No module named 'main'"
Make sure you're running tests from project root:
```bash
cd /path/to/RAG_LLMOPS
uv run pytest test/
```

### GROQ_API_KEY Not Found
This is expected - tests use mocks and don't require the real API key.

### Import Errors
Ensure pytest and dependencies are installed:
```bash
uv pip install pytest pytest-asyncio httpx
```

### Slow Tests
Integration tests take longer. Run unit tests only for fast feedback:
```bash
uv run pytest test/test_retrieval_unit.py
```

## Contributing New Tests

1. **Unit Tests**: Add to `test_retrieval_unit.py` for isolated component testing
2. **Integration Tests**: Add to `test_retrieval_integration.py` for workflow testing
3. **API Tests**: Add to `test_api_endpoints.py` for endpoint validation
4. **Mocking Examples**: Add to `test_mocking_strategies.py` for new patterns

### Test Template
```python
def test_something_with_clear_name(complete_mocks):
    """Docstring explaining what is being tested"""
    # Arrange
    pipeline = RetrievalPipeline()
    
    # Act
    result = pipeline.some_method()
    
    # Assert
    assert result is not None
```

## Summary

This test suite provides:
- ✅ Comprehensive coverage of RAG pipeline components
- ✅ Complete API endpoint validation
- ✅ Advanced mocking patterns and examples
- ✅ No external API dependencies (all mocked)
- ✅ Fast test execution (<5s for unit tests)
- ✅ Clear documentation and examples
- ✅ Easy extension for new test cases
