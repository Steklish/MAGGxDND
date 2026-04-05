# 🤝 Contributing Guide

Thank you for your interest in contributing to **MAGGxDND**! 🐉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)
- [Architecture Overview](#architecture-overview)

---

## 🌟 Code of Conduct

Be respectful, inclusive, and constructive. We're building something fun together. See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

---

## 🚀 Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/your-username/MAGGxDND.git
cd MAGGxDND
git remote add upstream https://github.com/original-owner/MAGGxDND.git
```

### 2. Set Up Environment

```bash
# Copy env template
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 3. Verify Setup

```bash
python start.py
# Visit http://localhost:8000
```

---

## 🔄 Development Workflow

### Branch Naming

```
feature/description        — New features
fix/description            — Bug fixes
docs/description           — Documentation changes
refactor/description       — Code refactoring
test/description           — Adding tests
```

Examples:
- `feature/websocket-combat-log`
- `fix/character-creation-validation`
- `docs/api-endpoints`

### Workflow

```bash
# Sync with main repo
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/my-feature

# Make changes, commit, push
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature
```

### Running Tests

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npm run test

# All tests
./run_tests.sh        # Linux/macOS
run_tests.bat         # Windows CMD
.\run_tests.ps1       # Windows PowerShell
```

---

## 📝 Coding Standards

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints for function signatures
- Docstrings for all public functions/classes
- Max line length: 120 characters

```python
async def create_session(self, name: str, max_players: int = 5) -> GameSession:
    """Create a new game session.

    Args:
        name: Session display name
        max_players: Maximum player count (default: 5)

    Returns:
        Created GameSession instance
    """
    ...
```

### TypeScript / React

- Functional components with hooks
- TypeScript strict mode — no `any`
- PascalCase for components, camelCase for functions
- Max line length: 120 characters

```tsx
interface CharacterCardProps {
    character: Character;
    onSelect: (id: number) => void;
}

export const CharacterCard: React.FC<CharacterCardProps> = ({ character, onSelect }) => {
    return (
        <div className="character-card" onClick={() => onSelect(character.id)}>
            {character.name}
        </div>
    );
};
```

### CSS

- BEM-like naming: `.block-element--modifier`
- Use CSS custom properties for theming
- Mobile-first responsive design

---

## 💬 Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, no logic change) |
| `refactor` | Code refactoring |
| `perf` | Performance improvement |
| `test` | Adding or fixing tests |
| `chore` | Build, CI, tooling |

### Examples

```
feat(character): add 13-step character creation wizard
fix(auth): resolve token refresh on 401 response
docs(api): add session API endpoint documentation
refactor(core): extract event pool into separate module
style(ui): fix alignment grid responsive breakpoints
```

---

## 🔄 Pull Requests

### Before Submitting

1. [ ] All tests pass
2. [ ] Code follows project style
3. [ ] No console errors or warnings
4. [ ] Commit messages follow convention
5. [ ] Branch is up to date with `main`

### PR Template

When opening a PR, fill out:

```markdown
## Description
What does this PR change and why?

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Backend tests pass
- [ ] Frontend tests pass
- [ ] Manual testing completed

## Screenshots (if UI change)
Before / After screenshots

## Related Issues
Closes #123
```

### Review Process

1. PR is opened
2. Automated checks run (CI)
3. At least one maintainer reviews
4. Address review comments
5. PR is merged

---

## 🏗 Architecture Overview

### Three Layers

```
┌─────────────────────────────────────┐
│         Frontend (React)            │  ← UI layer
├─────────────────────────────────────┤
│      Backend (FastAPI)              │  ← API + Auth
├─────────────────────────────────────┤
│    Core Engine (game logic)         │  ← Game rules
└─────────────────────────────────────┘
```

- **Frontend** — React 19 + TypeScript + Zustand
- **Backend** — FastAPI + SQLAlchemy + JWT auth
- **Core** — Game engine, AI DM, event system

See [docs/SERVER_ARCHITECTURE.md](./docs/SERVER_ARCHITECTURE.md) for details.

---

## ❓ Questions?

- Open a [Discussion](../../discussions)
- Check [existing issues](../../issues)
- Read the [documentation](./docs/)

---

<div align="center">

Happy coding! 🎲⚔️🐉

</div>
