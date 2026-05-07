# Contributing to Maximus.ai

Thank you for your interest in contributing to Maximus.ai!

## Development Setup

```bash
# Clone the repository
cd C:\Users\11vat\Desktop\agent007\maximus.ai

# Install in editable mode
pip install -e .

# Install development dependencies
pip install pytest pytest-asyncio ruff mypy pytest-cov
```

## Coding Standards

### Python Style
- Follow PEP 8
- Use type hints for all function signatures
- Use `pydantic` models for data structures
- Maximum line length: 100 characters

### Tools & Patterns
- All tools must inherit from `BaseTool` (in `tools/base.py`)
- Tools must define `ToolMetadata` with appropriate permission levels
- Register new tools in `tools/builtin/__init__.py`
- Use `async/await` for all tool `execute()` methods

### Documentation
- Add docstrings to all public classes and methods
- Update `ARCHITECTURE.md` when adding new components
- Add examples to `EXAMPLES.md` for user-facing features

## Testing

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/maximus --cov-report=term-missing

# Run specific test file
pytest tests/test_repo_adapters.py -v
```

### Writing Tests
- Place unit tests in `tests/unit/`
- Place integration tests in `tests/` (root level)
- Use `@pytest.mark.asyncio` for async tests
- Aim for 80%+ test coverage
- Mock external dependencies (Ollama, file system) when possible

### Test Naming
- Test files: `test_<module>.py`
- Test functions: `test_<functionality>_<scenario>`
- Example: `test_open_swe_tool_execute`

## Pull Request Process

1. Create a feature branch (`git checkout -b feature/my-feature`)
2. Make your changes
3. Run tests: `pytest tests/ -v`
4. Run linter: `ruff check src/`
5. Run type checker: `mypy src/`
6. Update documentation if needed
7. Submit pull request with clear description

## Adding New Tools

1. Create tool class in `src/maximus/tools/builtin/`
2. Inherit from `BaseTool`
3. Define `ToolMetadata` with appropriate fields
4. Implement `async execute(self, args, context)` method
5. Register in `src/maximus/tools/builtin/__init__.py`
6. Add tests in `tests/unit/test_tools.py`
7. Update tool count in `ARCHITECTURE.md` and `README.md`

## Adding New Features

### New Intelligence Components
- Place in `src/maximus/intelligence/`
- Update `ARCHITECTURE.md` with description
- Add integration tests

### New Memory Systems
- Place in `src/maximus/memory/`
- Ensure persistence at `~/.maximus/`
- Add tests for save/load functionality

## Issue Reporting

When reporting issues, please include:
- Python version
- Ollama version
- Maximus.ai version
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
