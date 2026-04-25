# Test Suite Architecture

## Overview

The test suite is organized around three levels of testing:

1. **Unit Tests** - Individual components in isolation
2. **Integration Tests** - Components working together
3. **API Tests** - HTTP endpoints and full workflows

All tests use mocks, stubs, and monkey patching to avoid external dependencies.

## Fixture Architecture

```
conftest.py (pytest configuration and fixtures)
├── Mock Classes
│   ├── MockEmbeddings - Returns fixed 384-dim vectors
│   ├── MockChatGroq - Context-aware LLM stub
│   └── MockFAISS - Document retrieval stub
├── Fixtures (basic)
│   ├── mock_embeddings - Single mock instance
│   ├── mock_llm - Single mock instance
│   └── mock_vectorstore - Single mock instance
└── Fixtures (compound)
    ├── patch_config - Patches configuration
    ├── patch_models - Patches LLM + embeddings
    ├── patch_vectorstore - Patches FAISS
    ├── patch_project_root - Patches file system
    └── complete_mocks - All patches combined
```

## Mock Object Hierarchy

```
RetrievalPipeline (what we test)
├── embeddings: MockEmbeddings (stub)
│   └── embed_query() → [0.1] * 384
├── llm: MockChatGroq (stub)
│   └── invoke() → Context-aware response
├── vectorstore: MockFAISS (stub)
│   └── as_retriever() → Returns k documents
└── chat_history_store: Dict (real, in-memory)
```

## Test File Structure

```
test/
├── __init__.py - Package marker
├── conftest.py - Shared fixtures and mocks
├── pytest.ini - Pytest configuration
├── test_retrieval_unit.py - Component testing
│   ├── Initialization tests
│   ├── Vectorstore loading tests
│   ├── Session management tests
│   ├── Document formatting tests
│   ├── Chain building tests
│   ├── Error handling tests
│   └── State management tests
├── test_retrieval_integration.py - Workflow testing
│   ├── RAG chain invocation tests
│   ├── Retriever behavior tests
│   ├── Conversational context tests
│   ├── Error recovery tests
│   ├── Response quality tests
│   └── Monkey patching demonstrations
├── test_api_endpoints.py - HTTP endpoint testing
│   ├── Health endpoint tests
│   ├── Web UI endpoint tests
│   ├── Chat endpoint tests
│   ├── Static files tests
│   ├── API documentation tests
│   ├── Error handling tests
│   ├── Response model tests
│   └── Concurrent request tests
├── test_mocking_strategies.py - Mocking patterns
│   ├── Mock object techniques
│   ├── Stub implementations
│   ├── Monkey patching patterns
│   ├── Partial mocking
│   ├── Property mocking
│   ├── Callable object mocking
│   └── Context manager mocking
├── README.md - Comprehensive guide
├── QUICKSTART.md - Quick reference
└── ARCHITECTURE.md - This file
```

## Mocking Strategies Used

### 1. Mock Objects (unittest.mock.Mock)
**Purpose**: Replace functions/methods with configurable stubs
**Use Case**: When you need to verify calls and return values

```python
mock = Mock(return_value="response")
mock.assert_called_once()
```

**Files**: All test files use Mock objects

### 2. Stub Classes
**Purpose**: Minimal implementations of real classes
**Use Case**: When you need realistic behavior without external calls

```python
class MockEmbeddings:
    def embed_query(self, q):
        return [0.1] * 384
```

**Files**: conftest.py (MockEmbeddings, MockChatGroq, MockFAISS)

### 3. Patch Decorators (@patch)
**Purpose**: Temporarily replace imports and functions
**Use Case**: Clean, context-aware patching with fixture isolation

```python
@patch("module.function", return_value=mock)
def test_something(mock_func):
    pass
```

**Files**: conftest.py uses @patch in fixtures

### 4. Monkey Patching
**Purpose**: Direct runtime replacement of attributes
**Use Case**: When you need to trace behavior or temporarily modify instance methods

```python
original = obj.method
obj.method = lambda x: "patched"
# ... test ...
obj.method = original
```

**Files**: test_retrieval_integration.py, test_mocking_strategies.py

### 5. Fixtures (pytest)
**Purpose**: Reusable test setup and mocking
**Use Case**: Share common mocks across multiple tests

```python
@pytest.fixture
def complete_mocks(...):
    yield {"embeddings": ..., "llm": ..., ...}
```

**Files**: conftest.py (defines all fixtures)

### 6. Side Effects
**Purpose**: Make mocks behave differently based on input
**Use Case**: Simulate complex behavior without full implementation

```python
mock.side_effect = lambda x: response_based_on(x)
```

**Files**: conftest.py (MockChatGroq), test files

## Test Execution Flow

### Unit Test Flow
```
1. Fixture Setup
   ├── complete_mocks (all mocks created)
   ├── patch_config (YAML config patched)
   ├── patch_models (get_llm, get_embeddings patched)
   ├── patch_vectorstore (FAISS.load_local patched)
   └── patch_project_root (get_project_root patched)

2. Test Execution
   ├── Create RetrievalPipeline (uses mocks)
   ├── Call methods (no external calls)
   └── Assert results/state

3. Fixture Teardown
   └── Patches automatically removed
```

### Integration Test Flow
```
1. Fixture Setup (complete_mocks)

2. Test Execution
   ├── Create RetrievalPipeline
   ├── Build RAG chain
   ├── Invoke chain with questions
   ├── Verify response and state
   └── Test conversational memory

3. Optional: Monkey Patching
   ├── Temporarily replace method
   ├── Test different behavior
   └── Restore original
```

### API Test Flow
```
1. Create TestClient
   └── Points to FastAPI app

2. Mock Dependencies
   ├── mock_rag_chain (global variable in main.py)
   ├── Patch into main module
   └── Ready for HTTP requests

3. Test Execution
   ├── Make HTTP requests
   ├── Verify status codes
   ├── Validate response structure
   └── Check JSON content

4. Cleanup
   └── TestClient closed
```

## Dependency Graph

```
Test Files
├── test_retrieval_unit.py
│   └── uses → complete_mocks (conftest.py)
├── test_retrieval_integration.py
│   └── uses → complete_mocks (conftest.py)
├── test_api_endpoints.py
│   ├── uses → TestClient(app)
│   ├── uses → mock_rag_chain (conftest.py)
│   └── patches → main.py module
└── test_mocking_strategies.py
    └── uses → complete_mocks (conftest.py)

conftest.py
├── defines → MockEmbeddings class
├── defines → MockChatGroq class
├── defines → MockFAISS class
└── provides → pytest fixtures

app (main.py)
├── imports → RetrievalPipeline
├── uses → global rag_chain variable
└── serves → /chat, /health, / endpoints
```

## No External Dependencies

### What's NOT Called
- ❌ Groq API (llama-3.1-8b-instant LLM)
- ❌ HuggingFace Hub (sentence-transformers embeddings)
- ❌ FAISS index files (actual vector database)
- ❌ OpenAI, Anthropic, or other LLMs
- ❌ Any HTTP endpoints

### Why Mocks?
- Tests run fast (<20s total)
- No API keys required
- Deterministic results
- Offline execution
- Cost-free testing
- Can simulate errors easily

## Assertion Patterns

### State Assertions
```python
assert pipeline.k == 3
assert "session_1" in pipeline.chat_history_store
assert len(pipeline.chat_history_store) == 2
```

### Response Type Assertions
```python
assert isinstance(response, str)
assert len(response) > 0
assert "frequency" in response.lower()
```

### Mock Call Assertions
```python
mock.assert_called_once()
mock.assert_called_with({"question": "test"})
assert mock.call_count == 3
mock.assert_has_calls([call("a"), call("b")])
```

### HTTP Response Assertions
```python
assert response.status_code == 200
assert "json" in response.headers.get("content-type", "")
data = response.json()
assert "question" in data
```

## Error Handling Tests

### Expected Exceptions
```python
with pytest.raises(EnergyDocsException):
    RetrievalPipeline()  # Missing vectorstore

with pytest.raises(FileNotFoundError):
    # Bad vectorstore path
```

### HTTP Error Codes
```python
assert response.status_code == 422  # Validation error
assert response.status_code == 503  # Service unavailable
assert response.status_code == 404  # Not found
```

## Extension Points

### Adding New Unit Tests
1. Create test class in test_retrieval_unit.py
2. Use `complete_mocks` fixture
3. Follow "Arrange → Act → Assert" pattern
4. Assert state and returns

### Adding New Integration Tests
1. Create test class in test_retrieval_integration.py
2. Use `complete_mocks` fixture
3. Build chain and invoke
4. Test multi-turn conversations and history

### Adding New API Tests
1. Create test class in test_api_endpoints.py
2. Use `client` fixture (TestClient)
3. Mock rag_chain with patch
4. Make HTTP requests and assert responses

### Adding New Mocking Examples
1. Create test class in test_mocking_strategies.py
2. Demonstrate the mocking pattern
3. Include setup, test, and assertions
4. Document the use case

## Performance Characteristics

### Test Execution Time
```
Unit Tests: ~1-3 seconds
├── 25 tests
├── Mostly assertion-based
└── Minimal setup/teardown

Integration Tests: ~5-10 seconds
├── 19 tests
├── Chain invocation overhead
└── Multi-turn conversations

API Tests: ~5-10 seconds
├── 31 tests
├── TestClient setup
└── HTTP request simulation

Total: ~15-20 seconds for full suite
```

### Memory Usage
- Minimal (all mocks, no real models)
- No embedding model loaded
- No LLM weights loaded
- FAISS index mocked (no index files)

## Summary

The test suite provides:
- ✅ 92 comprehensive tests
- ✅ 3 levels of testing (unit, integration, API)
- ✅ Advanced mocking patterns (mocks, stubs, monkey patching)
- ✅ Zero external dependencies
- ✅ Fast execution (~15-20 seconds)
- ✅ Clear documentation and examples
- ✅ Easy to extend with new tests
