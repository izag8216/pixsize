# Contributing to pixsize

Thank you for your interest in contributing to pixsize!

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest tests/ -v`)
6. Run linter (`ruff check src/ tests/`)
7. Commit with a descriptive message
8. Open a Pull Request

## Development Setup

```bash
pip install -e ".[dev]"
pytest tests/ -v --cov=pixsize
ruff check src/ tests/
```

## Code Style

- Follow PEP 8
- Use type hints
- Keep functions under 50 lines
- Maintain 80%+ test coverage

## Reporting Issues

Please use the [GitHub issue tracker](https://github.com/izag8216/pixsize/issues) and include:

- Python version
- pixsize version
- Steps to reproduce
- Expected vs actual behavior
