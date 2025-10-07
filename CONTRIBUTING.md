# Contributing to Digital Calendar

Thank you for your interest in contributing to Digital Calendar! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/digital-calendar.git
   cd digital-calendar
   ```

3. Set up development environment:
   ```bash
   # Backend
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt

   # Frontend
   cd ../frontend
   npm install
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

### Creating a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or changes

### Making Changes

1. Make your changes
2. Write/update tests
3. Run tests locally
4. Format code:
   ```bash
   # Python
   black backend/
   isort backend/
   flake8 backend/

   # TypeScript
   cd frontend
   npm run lint
   npm run format
   ```

5. Commit your changes:
   ```bash
   git commit -m "feat: add new feature"
   ```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks

Examples:
```
feat: add Google Tasks integration
fix: resolve OAuth redirect issue
docs: update installation instructions
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Run all tests with coverage
pytest --cov=backend
npm test -- --coverage
```

### Submitting a Pull Request

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request on GitHub
3. Fill out the PR template
4. Wait for review and CI checks
5. Address review feedback
6. Once approved, your PR will be merged

## Code Style

### Python
- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints
- Write docstrings for all public functions
- Keep functions focused and small

### TypeScript
- Follow Airbnb style guide
- Use Prettier for formatting
- Use explicit types (avoid `any`)
- Write JSDoc comments for components
- Use functional components with hooks

## Testing

### Backend Testing
- Write unit tests for all new functions
- Test edge cases and error conditions
- Use pytest fixtures for setup
- Aim for >80% code coverage

### Frontend Testing
- Write tests for components
- Test user interactions
- Test API integration
- Use React Testing Library

## Documentation

- Update README.md if adding features
- Add JSDoc/docstrings to new code
- Update API documentation
- Include examples where helpful

## Questions?

- Open an issue for questions
- Check existing issues and PRs
- Review documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
