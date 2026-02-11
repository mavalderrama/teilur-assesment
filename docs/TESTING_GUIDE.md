

# Testing Guide

Comprehensive guide for running and writing tests for the AWS AI Agent project.

---

## Quick Start

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── domain/             # Domain entity tests
│   │   ├── test_stock_price.py
│   │   ├── test_document.py
│   │   └── test_query_result.py
│   ├── application/        # Use case tests
│   │   ├── test_get_realtime_stock_price.py
│   │   ├── test_get_historical_stock_price.py
│   │   └── test_query_documents.py
│   └── infrastructure/     # Infrastructure tests (with mocks)
└── integration/            # Integration tests (real dependencies)
    ├── test_yfinance_repository.py
    └── test_agent_end_to_end.py
```

---

## Test Categories

### Unit Tests (Fast, Isolated)

**Location:** `tests/unit/`

**Characteristics:**
- ✅ No external dependencies
- ✅ Use mocks for all dependencies
- ✅ Fast execution (< 1ms per test)
- ✅ Run on every commit

**Run unit tests only:**
```bash
pytest tests/unit/
```

**Example:**
```python
from unittest.mock import AsyncMock, Mock
import pytest

def test_use_case_with_mocked_repository():
    # Arrange
    mock_repo = Mock(spec=IStockRepository)
    mock_repo.get_realtime_price = AsyncMock(return_value=stock_price)
    use_case = GetRealtimeStockPriceUseCase(mock_repo)

    # Act
    result = await use_case.execute("AMZN")

    # Assert
    assert result == stock_price
    mock_repo.get_realtime_price.assert_called_once_with("AMZN")
```

### Integration Tests (Real Dependencies)

**Location:** `tests/integration/`

**Characteristics:**
- ⚠️ May require external services (yfinance, AWS)
- ⚠️ Slower execution
- ⚠️ May fail due to network issues
- ✅ Test real behavior

**Run integration tests only:**
```bash
pytest tests/integration/ -m integration
```

**Skip integration tests:**
```bash
pytest -m "not integration"
```

**Example:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_stock_price_fetch():
    # Uses real yfinance API
    repository = YFinanceStockRepository()
    price = await repository.get_realtime_price("AMZN")

    assert price.symbol == "AMZN"
    assert price.price > 0
```

---

## Test Markers

Tests are marked with pytest markers for selective execution:

| Marker | Purpose | Usage |
|--------|---------|-------|
| `@pytest.mark.unit` | Unit test | Fast, isolated tests |
| `@pytest.mark.integration` | Integration test | Tests with real services |
| `@pytest.mark.slow` | Slow test | Tests taking > 1 second |
| `@pytest.mark.requires_aws` | Requires AWS | Tests needing AWS credentials |

**Run specific markers:**
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run tests requiring AWS
pytest -m requires_aws
```

---

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test File
```bash
pytest tests/unit/domain/test_stock_price.py
```

### Specific Test Class
```bash
pytest tests/unit/domain/test_stock_price.py::TestStockPrice
```

### Specific Test Method
```bash
pytest tests/unit/domain/test_stock_price.py::TestStockPrice::test_create_valid_stock_price
```

### With Coverage
```bash
# Generate coverage report
pytest --cov=src

# HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=src --cov-report=term-missing
```

### Verbose Output
```bash
# Show all test names
pytest -v

# Show print statements
pytest -s

# Both
pytest -vs
```

### Stop on First Failure
```bash
pytest -x
```

### Run Last Failed Tests
```bash
pytest --lf
```

### Parallel Execution
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers
pytest -n 4
```

---

## Test Coverage

### Current Coverage Targets

- **Overall:** ≥ 70%
- **Domain Layer:** ≥ 90% (critical business logic)
- **Application Layer:** ≥ 85% (use cases)
- **Infrastructure Layer:** ≥ 60% (harder to test)

### Check Coverage

```bash
# Generate report
pytest --cov=src --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=70
```

### Coverage Configuration

See `pytest.ini` for coverage settings:
```ini
[coverage:run]
source = src
omit =
    */tests/*
    */test_*

[coverage:report]
exclude_lines =
    pragma: no cover
    raise NotImplementedError
```

---

## Writing Tests

### Test Structure (AAA Pattern)

```python
def test_something():
    # Arrange - Set up test data and mocks
    input_data = "test"
    expected_output = "result"

    # Act - Execute the code under test
    actual_output = function_under_test(input_data)

    # Assert - Verify the results
    assert actual_output == expected_output
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

### Mocking Dependencies

```python
from unittest.mock import AsyncMock, Mock

def test_with_mocked_dependency():
    # Mock synchronous method
    mock_service = Mock()
    mock_service.get_data.return_value = "data"

    # Mock async method
    mock_async = AsyncMock()
    mock_async.fetch_data.return_value = "async_data"

    # Use in test
    result = await function_with_dependency(mock_async)
    mock_async.fetch_data.assert_called_once()
```

### Parametrized Tests

```python
@pytest.mark.parametrize("symbol,expected", [
    ("AMZN", "AMZN"),
    ("amzn", "AMZN"),  # Should normalize to uppercase
    ("  AMZN  ", "AMZN"),  # Should strip whitespace
])
def test_symbol_normalization(symbol, expected):
    result = normalize_symbol(symbol)
    assert result == expected
```

### Testing Exceptions

```python
import pytest

def test_raises_exception():
    with pytest.raises(ValueError, match="must be positive"):
        function_that_raises(-1)
```

### Fixtures

```python
@pytest.fixture
def mock_repository():
    """Reusable mock repository."""
    mock = Mock(spec=IStockRepository)
    mock.get_realtime_price = AsyncMock(return_value=StockPrice(...))
    return mock

def test_using_fixture(mock_repository):
    use_case = GetRealtimeStockPriceUseCase(mock_repository)
    # ... test code
```

---

## Test Examples by Layer

### Domain Layer Tests

**Test immutability:**
```python
def test_entity_is_immutable():
    entity = StockPrice(symbol="AMZN", price=Decimal("100"), timestamp=datetime.now())

    with pytest.raises(AttributeError):
        entity.symbol = "AAPL"  # Should fail - frozen dataclass
```

**Test validation:**
```python
def test_entity_validates_inputs():
    with pytest.raises(ValueError, match="cannot be empty"):
        StockPrice(symbol="", price=Decimal("100"), timestamp=datetime.now())

    with pytest.raises(ValueError, match="cannot be negative"):
        StockPrice(symbol="AMZN", price=Decimal("-10"), timestamp=datetime.now())
```

### Application Layer Tests

**Test use case with mocked repository:**
```python
@pytest.mark.asyncio
async def test_use_case_delegates_to_repository():
    # Arrange
    mock_repo = Mock(spec=IStockRepository)
    expected = StockPrice(...)
    mock_repo.get_realtime_price = AsyncMock(return_value=expected)
    use_case = GetRealtimeStockPriceUseCase(mock_repo)

    # Act
    result = await use_case.execute("AMZN")

    # Assert
    assert result == expected
    mock_repo.get_realtime_price.assert_called_once_with("AMZN")
```

**Test validation:**
```python
@pytest.mark.asyncio
async def test_use_case_validates_inputs():
    use_case = GetRealtimeStockPriceUseCase(Mock())

    with pytest.raises(ValueError, match="must be a non-empty string"):
        await use_case.execute("")

    with pytest.raises(ValueError, match="must be a non-empty string"):
        await use_case.execute(None)
```

### Infrastructure Layer Tests

**Integration test with real service:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_repository_fetches_real_data():
    repository = YFinanceStockRepository()
    price = await repository.get_realtime_price("AMZN")

    assert price.symbol == "AMZN"
    assert price.price > 0
    assert price.currency == "USD"
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run unit tests
        run: |
          pytest tests/unit/ --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Troubleshooting

### Tests Fail Due to Missing Modules

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Integration Tests Fail

**Solution:**
```bash
# Skip integration tests
pytest -m "not integration"

# Or run only unit tests
pytest tests/unit/
```

### AWS Tests Fail

**Solution:**
```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Or skip AWS tests
pytest -m "not requires_aws"
```

### Coverage Too Low

**Solution:**
```bash
# See which files need more tests
pytest --cov=src --cov-report=term-missing

# Focus on files with low coverage
pytest --cov=src/domain --cov-report=html
open htmlcov/index.html
```

---

## Best Practices

### DO ✅

- Write tests before fixing bugs (TDD)
- Use descriptive test names (test_what_when_expected)
- Test edge cases and error conditions
- Mock external dependencies
- Keep tests fast and isolated
- Use fixtures for common setup
- Follow AAA pattern (Arrange, Act, Assert)
- Test behavior, not implementation

### DON'T ❌

- Test implementation details
- Use real external services in unit tests
- Write slow tests
- Ignore failing tests
- Test third-party libraries
- Have tests that depend on each other
- Commit code without running tests

---

## Test Metrics

### Current Test Statistics

- **Total Tests:** 40+
- **Domain Layer:** 20+ tests (entities)
- **Application Layer:** 15+ tests (use cases)
- **Integration:** 5+ tests (real services)
- **Coverage:** ≥ 70%

### Run Test Metrics

```bash
# Count tests
pytest --collect-only | grep "test_"

# Test duration report
pytest --durations=10

# Coverage by module
pytest --cov=src --cov-report=term-missing
```

---

## Summary

### Quick Commands

```bash
# Run all tests
pytest

# Unit tests only (fast)
pytest tests/unit/

# With coverage
pytest --cov=src --cov-report=html

# Skip slow tests
pytest -m "not slow"

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Test Pyramid

```
         /\
        /  \       E2E Tests (Few, Slow)
       /────\
      / Inte \     Integration Tests (Some, Medium)
     /────────\
    /   Unit   \   Unit Tests (Many, Fast)
   /────────────\
```

**Follow the test pyramid:**
- Many unit tests (fast, isolated)
- Some integration tests (real services)
- Few end-to-end tests (full system)

---

**Happy Testing!** 🧪✅
