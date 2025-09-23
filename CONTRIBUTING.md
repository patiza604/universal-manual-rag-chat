# Contributing to Universal Manual RAG Chat

Thank you for your interest in contributing to Universal Manual RAG Chat! We welcome contributions from the community and are excited to see what you'll build.

## 🎯 How to Contribute

### 🐛 Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/patiza604/universal-manual-rag-chat/issues) to avoid duplicates. When creating a bug report, include:

- **Clear description** of the issue
- **Steps to reproduce** the behavior
- **Expected vs actual behavior**
- **Environment details** (OS, Python/Flutter versions, etc.)
- **Screenshots or logs** if applicable

### 💡 Suggesting Features

We love feature suggestions! Please:

1. Check [existing feature requests](https://github.com/patiza604/universal-manual-rag-chat/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
2. Create a detailed issue with:
   - **Problem description** - What need does this address?
   - **Proposed solution** - How should it work?
   - **Alternatives considered** - Other approaches you've thought about
   - **Additional context** - Any other relevant information

### 🔧 Code Contributions

#### Development Setup

1. **Fork the repository**
```bash
git clone https://github.com/patiza604/universal-manual-rag-chat.git
cd universal-manual-rag-chat
```

2. **Backend setup**
```bash
cd chatbot_backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend setup**
```bash
cd chatbot_frontend
flutter pub get
```

4. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

#### Development Guidelines

##### Code Style

**Python (Backend)**
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints where possible
- Add docstrings for all functions and classes
- Run linting: `python -m pylint app/ agent/ api/`

**Dart/Flutter (Frontend)**
- Follow [Dart style guide](https://dart.dev/guides/language/effective-dart/style)
- Use `flutter analyze` before committing
- Format code with `dart format .`

**General**
- Write descriptive commit messages
- Keep commits focused and atomic
- Add comments for complex logic
- Update documentation for new features

##### Testing

**Backend Testing**
```bash
# Run enhanced RAG system tests
python test_simple.py
python test_customer_queries.py

# API testing
python -m pytest tests/  # If pytest is set up

# Manual adherence testing
curl -X POST "http://localhost:8080/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"message": "test query"}'
```

**Frontend Testing**
```bash
# Flutter tests
cd chatbot_frontend
flutter test

# Widget tests
flutter test test/widget_test.dart
```

##### Documentation

- Update README.md for new features
- Add/update docstrings and comments
- Update API documentation if endpoints change
- Add examples for new functionality

#### Pull Request Process

1. **Ensure your branch is up to date**
```bash
git checkout main
git pull origin main
git checkout feature/your-feature-name
git rebase main
```

2. **Test thoroughly**
   - Run all relevant tests
   - Test manual adherence if AI-related changes
   - Verify both backend and frontend work

3. **Create the pull request**
   - Use a descriptive title
   - Reference related issues with `Fixes #123`
   - Include a detailed description of changes
   - Add screenshots for UI changes

4. **Review process**
   - Address reviewer feedback promptly
   - Keep discussions focused and constructive
   - Update tests/docs as requested

## 🏗️ Architecture Guidelines

### Enhanced RAG System

When contributing to the RAG system:

- **Understand the 6-level hierarchy**: L0 (quick facts) → L4 (cross-refs)
- **Preserve manual adherence**: Ensure AI responses stay strictly within manual content
- **Test query classification**: Verify your changes don't break the 75% accuracy
- **Performance matters**: Keep search response times under 1ms

### Multi-Component Changes

For changes affecting multiple components:

1. **Backend first**: Implement API changes
2. **Test backend**: Ensure endpoints work correctly
3. **Frontend updates**: Update UI to use new backend features
4. **Integration testing**: Test the full flow
5. **Documentation**: Update all relevant docs

## 🎨 Areas for Contribution

### 🔥 High Priority

- **Manual Processing**: Support for new document formats (PDF, Word, etc.)
- **Query Classification**: Improve accuracy beyond 75%
- **Mobile App**: Enhanced Flutter mobile experience
- **Performance**: Optimize search response times
- **Testing**: Comprehensive test coverage

### 🌟 Feature Areas

- **Authentication**: Additional auth providers
- **Analytics**: Usage metrics and insights
- **Accessibility**: Screen reader support, keyboard navigation
- **Internationalization**: Multi-language support
- **API**: GraphQL endpoints, webhooks

### 🐛 Bug Fixes

- **Cross-platform**: Flutter web/mobile compatibility
- **Error handling**: Better error messages and recovery
- **Memory optimization**: Reduce resource usage
- **Image handling**: Improve Firebase Storage integration

## 📋 Development Workflow

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

### Commit Messages

Use conventional commits format:

```
type(scope): brief description

Detailed explanation of what and why, not how.

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(rag): add support for PDF manual processing`
- `fix(auth): resolve Firebase authentication timeout`
- `docs(readme): update installation instructions`

## 🤝 Community Guidelines

### Code of Conduct

- **Be respectful**: Treat everyone with kindness and respect
- **Be inclusive**: Welcome people of all backgrounds and experience levels
- **Be constructive**: Provide helpful feedback and suggestions
- **Be patient**: Remember that everyone is learning

### Getting Help

- **Discord/Slack**: Join our community chat (link in README)
- **Issues**: Use GitHub issues for technical questions
- **Discussions**: Use GitHub discussions for general questions
- **Wiki**: Check the project wiki for detailed guides

## 🏆 Recognition

Contributors will be:
- Added to the README contributors section
- Mentioned in release notes for significant contributions
- Invited to the contributors channel in our community chat

## 📚 Resources

### Learning Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Flutter Documentation](https://flutter.dev/docs)
- [Google Cloud AI](https://cloud.google.com/ai)
- [Firebase Documentation](https://firebase.google.com/docs)

### Project-Specific
- [Enhanced RAG System Guide](chatbot_backend/training/docs/UNIVERSAL_RAG_SYSTEM_GUIDE.md)
- [CLAUDE.md](CLAUDE.md) - Development guidelines
- [API Documentation](docs/api.md)

---

Thank you for contributing to Universal Manual RAG Chat! Your efforts help make technical support more accessible and reliable for everyone. 🚀