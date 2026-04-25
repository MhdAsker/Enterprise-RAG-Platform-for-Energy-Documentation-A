# Test Suite Quick Start

## One-Minute Setup

```bash
# Install pytest and dependencies
uv pip install pytest pytest-asyncio pytest-timeout pytest-cov httpx

# Run all tests (no API key needed - all mocked)
uv run pytest test/ -v

# Run specific test module
uv run pytest test/test_retrieval_unit.py -v

# Run with coverage
uv run pytest test/ --cov=energy_docs_chat --cov-report=html
```

## Test Overview

| Module | Tests | Focus |
|--------|-------|-------|
| **test_retrieval_unit.py** | 25 | Individual components with mocks |
| **test_retrieval_integration.py** | 19 | Full RAG chain workflows |
| **test_api_endpoints.py** | 31 | FastAPI endpoints |
| **test_mocking_strategies.py** | 17 | Advanced mocking patterns |
| **Total** | **92** | Comprehensive coverage |

## What Gets Tested

✅ **RetrievalPipeline**
- Initialization with config
- Vectorstore loading
- Session management
- Chain building

✅ **RAG Chain**
- Simple questions
- Multi-turn conversations
- Session isolation
- Document retrieval
- Error handling

✅ **FastAPI Endpoints**
- GET / (HTML UI)
- GET /health (status)
- POST /chat (RAG inference)
- GET /static/* (CSS, JS)
- GET /docs (API docs)

✅ **Mocking Strategies**
- Mock objects with return values
- Stubs with behavior
- Monkey patching
- Context managers
- Side effects and assertions

## Running Tests

### All Tests
```bash
uv run pytest test/
```

### Unit Tests Only (Fast)
```bash
uv run pytest test/test_retrieval_unit.py
```

### Integration Tests Only
```bash
uv run pytest test/test_retrieval_integration.py
```

### API Tests Only
```bash
uv run pytest test/test_api_endpoints.py
```

### Mocking Examples Only
```bash
uv run pytest test/test_mocking_strategies.py
```

### Single Test
```bash
uv run pytest test/test_retrieval_unit.py::TestRetrievalPipelineInitialization::test_init_success_with_mocks -v
```

### Verbose Output
```bash
uv run pytest test/ -v  # Show test names and results
```

### Very Verbose
```bash
uv run pytest test/ -vv  # Show more details
```

### With Print Statements (debug)
```bash
uv run pytest test/ -v -s  # Show print() output
```

## Example Test Runs

### Run Only Initialization Tests
```bash
uv run pytest test/test_retrieval_unit.py::TestRetrievalPipelineInitialization -v
```

### Run Only Session Tests
```bash
uv run pytest test/test_retrieval_unit.py::TestSessionHistory -v
```

### Run RAG Chain Tests
```bash
uv run pytest test/test_retrieval_integration.py::TestRAGChainInvocation -v
```

### Run Chat Endpoint Tests
```bash
uv run pytest test/test_api_endpoints.py::TestChatEndpoint -v
```

## Understanding Test Mocks

### Complete Mocks (`complete_mocks` fixture)
Patches everything needed for RetrievalPipeline:
- Config
- Embeddings model
- LLM (ChatGroq)
- Vectorstore (FAISS)
- Project root

```python
def test_something(complete_mocks):  # All patched automatically
    pipeline = RetrievalPipeline()
    # Everything works with mocks
```

### Selective Mocks
Patch only what you need:

```python
def test_with_config_only(patch_config):
    # Only config is patched
    with patch("model_loader.get_llm", return_value=...):
        # Now LLM is also patched
```

## Key Mocking Patterns

### Mock with Return Value
```python
pipeline.llm.invoke = Mock(return_value="response")
```

### Mock with Side Effect
```python
pipeline.llm.invoke = Mock(
    side_effect=lambda x: "freq" if "frequency" in str(x) else "other"
)
```

### Stub Implementation
```python
class FakeLLM:
    def invoke(self, x):
        return "stub response"

pipeline.llm = FakeLLM()
```

### Monkey Patch
```python
original = pipeline.llm.invoke
pipeline.llm.invoke = lambda x: "patched"
# ... test ...
pipeline.llm.invoke = original
```

### Assert Mock Was Called
```python
mock_llm = Mock(return_value="result")
mock_llm.invoke({"question": "test"})
mock_llm.assert_called_once()
mock_llm.assert_called_with({"question": "test"})
```

## Test Examples

### Unit Test Example
```python
def test_init_success_with_mocks(complete_mocks):
    """Test successful initialization"""
    pipeline = RetrievalPipeline()
    assert pipeline is not None
    assert pipeline.k == 3
```

### Integration Test Example
```python
def test_chain_invoke_with_simple_question(complete_mocks):
    """Test RAG chain invocation"""
    pipeline = RetrievalPipeline()
    chain = pipeline.build_chain()
    response = chain.invoke(
        {"question": "What is frequency?"},
        config={"configurable": {"session_id": "test_1"}}
    )
    assert isinstance(response, str)
```

### API Test Example
```python
def test_chat_returns_200_with_valid_request(client, mock_rag_chain):
    """Test chat endpoint"""
    with patch("main.rag_chain", mock_rag_chain):
        response = client.post(
            "/chat",
            json={"question": "Test", "session_id": "test"}
        )
        assert response.status_code == 200
```

## Troubleshooting

### Tests Not Found
```bash
# Run from project root
cd /path/to/RAG_LLMOPS
uv run pytest test/
```

### Import Error: "No module named 'energy_docs_chat'"
```bash
# Ensure you're in project root and python path is set
uv run pytest test/
```

### GROQ_API_KEY Not Set
✅ This is expected - tests don't use real API

### Tests Hang/Timeout
```bash
# Add timeout
uv run pytest test/ --timeout=10
```

### Want to See More Details
```bash
# Verbose + show print statements
uv run pytest test/ -vv -s
```

## Next Steps

1. **Run tests**: `uv run pytest test/ -v`
2. **Explore code**: Check test files to understand patterns
3. **Add tests**: Create new tests following same patterns
4. **Check coverage**: `uv run pytest test/ --cov=energy_docs_chat`

## Test Statistics

```
92 total tests
├── 25 unit tests (fast, <1s)
├── 19 integration tests (medium, 1-5s)
├── 31 API tests (medium, 1-5s)
└── 17 mocking examples (fast, <1s)

Total runtime: ~10-20 seconds
API key required: ❌ (No - all mocked)
External services: ❌ (No - all mocked)
```
