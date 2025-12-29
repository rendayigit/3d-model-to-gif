# Contributing to Model Preview Generator

Thank you for your interest in contributing to Model Preview Generator! This document provides guidelines and information for contributors.

## 🌟 Ways to Contribute

- **Bug Reports**: Found a bug? Please open an issue!
- **Feature Requests**: Have an idea? We'd love to hear it!
- **Code Contributions**: Submit a pull request
- **Documentation**: Help improve our docs
- **Testing**: Help test on different platforms

## 🚀 Getting Started

### Setting Up Development Environment

1. **Fork and clone the repository:**

   ```bash
   git clone https://github.com/rendayigit/3d-model-to-gif.git
   cd 3d-model-to-gif
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

3. **Install development dependencies:**

   ```bash
   pip install -e ".[dev]"
   ```

4. **Create a feature branch:**

   ```bash
   git checkout -b feature/your-feature-name
   ```

### Project Structure

```
3d-model-to-gif/
├── main.py              # Application entry point
├── src/
│   ├── __init__.py      # Package metadata
│   ├── app.py           # GUI application (PySide6)
│   └── renderer.py      # 3D rendering engine
├── tests/               # Unit tests
├── docs/                # Documentation
├── requirements.txt     # Production dependencies
├── pyproject.toml       # Project configuration
└── README.md
```

## 📝 Code Style

We follow these coding standards:

### Python Style Guide

- **Formatter**: [Black](https://black.readthedocs.io/) with line length 100
- **Linter**: [Ruff](https://docs.astral.sh/ruff/)
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Google-style docstrings for all public functions

### Before Committing

Run these commands to ensure code quality:

```bash
# Format code
black src/ tests/

# Check for linting issues
ruff check src/ tests/

# Type checking
mypy src/

# Run tests
pytest
```

### Example Code Style

```python
def render_preview(
    model_path: str,
    output_path: str,
    width: int = 800,
    height: int = 800,
) -> str:
    """
    Render a preview image of a 3D model.
    
    Args:
        model_path: Path to the 3D model file.
        output_path: Path where the rendered image will be saved.
        width: Output image width in pixels.
        height: Output image height in pixels.
        
    Returns:
        Path to the saved image file.
        
    Raises:
        FileNotFoundError: If the model file doesn't exist.
        ValueError: If dimensions are invalid.
    """
    # Implementation here
    pass
```

## 🔧 Making Changes

### Adding a New Feature

1. **Discuss first**: For major features, open an issue to discuss before coding
2. **Write tests**: Add tests for new functionality
3. **Update docs**: Update README if needed
4. **Follow style**: Ensure code passes all style checks

### Bug Fixes

1. **Reference the issue**: Link to the issue being fixed
2. **Add a test**: Add a test that fails without the fix
3. **Keep it focused**: One fix per pull request

## 📤 Submitting Pull Requests

### PR Checklist

- [ ] Code follows the project style guide
- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`black`)
- [ ] Linting passes (`ruff check`)
- [ ] Type hints are correct (`mypy`)
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear and descriptive

### Commit Message Format

Use clear, descriptive commit messages:

```
feat: add transparent background support

- Add alpha channel rendering option
- Update background preset configuration
- Add tests for transparent output
```

Prefixes:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### Pull Request Process

1. Update your branch with the latest `main`
2. Ensure all checks pass
3. Fill out the PR template completely
4. Request review from maintainers
5. Address any feedback
6. Squash commits if requested

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_renderer.py

# Run tests with verbose output
pytest -v
```

### Writing Tests

Place tests in the `tests/` directory with names matching `test_*.py`:

```python
import pytest
from src.renderer import CameraSettings, create_rotation_matrix

def test_camera_settings_defaults():
    """Test default camera settings values."""
    camera = CameraSettings()
    assert camera.zoom == 2.0
    assert camera.offset_x == 0.0
    assert camera.offset_y == 0.0

def test_rotation_matrix_y_axis():
    """Test Y-axis rotation matrix generation."""
    matrix = create_rotation_matrix(90, "y")
    assert matrix.shape == (4, 4)
```

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Operating System**: (e.g., Ubuntu 22.04, Windows 11)
2. **Python Version**: (e.g., Python 3.11.5)
3. **Steps to Reproduce**: Detailed steps to reproduce the issue
4. **Expected Behavior**: What you expected to happen
5. **Actual Behavior**: What actually happened
6. **Error Messages**: Full error traceback if applicable
7. **Model File**: If possible, provide a sample model file

### Bug Report Template

```markdown
**Environment:**
- OS: 
- Python version: 
- Package versions: (output of `pip freeze`)

**Description:**
Clear description of the bug

**Steps to Reproduce:**
1. Step one
2. Step two
3. ...

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Error Messages:**
```

Paste full error traceback here

```

**Additional Context:**
Any other relevant information
```

## 💡 Feature Requests

We welcome feature suggestions! When proposing a feature:

1. **Check existing issues**: Make sure it's not already requested
2. **Explain the use case**: Why is this feature needed?
3. **Describe the solution**: How do you envision it working?
4. **Consider alternatives**: Are there other ways to achieve this?

## 📜 Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Accept constructive criticism gracefully
- Focus on what's best for the community

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Publishing others' private information
- Other unprofessional conduct

## 📞 Getting Help

- **Questions**: Open a discussion or issue
- **Chat**: Join our community discussions
- **Email**: Contact maintainers for sensitive issues

## 🎉 Recognition

Contributors will be recognized in:

- The project README
- Release notes
- Contributors file

Thank you for contributing to Model Preview Generator! 🙏
