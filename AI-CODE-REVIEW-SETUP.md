# AI Code Review Setup - Phase 4

**Date:** 2026-02-10 11:00 UTC
**Phase:** Testing Foundation - Phase 4
**Status:** 📋 IMPLEMENTATION IN PROGRESS

---

## Overview

Implementing AI-powered code review workflow using:
1. **Cursor CLI** - AI code analysis and suggestions
2. **Pre-commit hooks** - Automated code quality checks
3. **Pull request templates** - Structured code reviews

---

## Part 1: Pre-commit Hooks Setup

### Installation

```bash
# Install pre-commit framework
pip install pre-commit

# Create pre-commit configuration
cat > .pre-commit-config.yaml <<'EOF'
repos:
  # General checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: debug-statements

  # Python linting
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        additional_dependencies:
          - flake8-django
          - flake8-bugbear
        args: ['--max-line-length=100', '--exclude=*/migrations/*']

  # Security checks
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ['-ll']
        files: ^gaastats/

  # Django checks
  - repo: https://github.com/adamchainz/django-upgrade
    rev: 1.16.0
    hooks:
      - id: django-upgrade
        args: ['--target-version', '5.0']

  # Type checking (optional, if using type hints)
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - django-stubs
        args: ['--ignore-missing-imports']
EOF

# Install pre-commit hooks
pre-commit install
```

### Pre-commit Hook Categories

1. **Code Style**
   - Trailing whitespace removal
   - End-of-file normalization
   - Merge conflict detection

2. **Python Quality**
   - Flake8 linting (PEP 8, style, complexity)
   - Django-specific checks
   - Bug detection (flake8-bugbear)

3. **Security**
   - Bandit static analysis
   - Hardcoded secret detection
   - SQL injection prevention

4. **Type Safety**
   - MyPy type checking
   - Django stubs integration

---

## Part 2: Cursor CLI Code Review Workflow

### Automated Pre-commit Code Review

```bash
# Run Cursor AI review on staged files
git diff --cached --name-only | grep '\.py$' | while read file; do
  echo "Reviewing $file..."
  agent -p "Review $file for:
1. Code clarity and readability
2. Potential bugs or edge cases
3. Security vulnerabilities
4. Django best practices
5. Performance optimization opportunities

Provide specific actionable suggestions."
done
```

### Interactive Code Review Session

```bash
# Start Cursor CLI for interactive review
agent
# Then use commands:
@gastats/views/
@gastats/models/
Review these files for consistency, security, and Django best practices.
```

### Git Integration with Cursor

```bash
# Generate commit message with AI
agent -p "Generate a conventional commit message for these changes:
$(git diff --staged --stat)"

# Review entire branch
agent -p "Review the changes in the current branch against main. Focus on:
1. Breaking changes
2. Security issues
3. Performance impact
4. Test coverage
5. Documentation needs"

# Run security audit
agent -p "Audit this codebase for security vulnerabilities:
1. SQL injection
2. XSS vulnerabilities
3. CSRF issues
4. Authentication/authorization flaws"
```

---

## Part 3: Pull Request Review Templates

### PR Template (.github/pull_request_template.md)

```markdown
## Description
[Description of changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Pre-commit checks passed
- [ ] No hardcoded secrets
- [ ] AI code review completed

## Review Notes
[Any notes for reviewers]

## Cursor CLI Review Summary
[Paste AI review output here]
```

### Code Review Checklist

**Code Quality:**
- [ ] Follows PEP 8 style guide
- [ ] Functions/classes have docstrings
- [ ] Variable names are descriptive
- [ ] Magic numbers replaced with constants
- [ ] Code is DRY (Don't Repeat Yourself)

**Django Best Practices:**
- [ ] Uses Django ORM (no raw SQL unless necessary)
- [ ] Proper use of signals
- [ ] Database migrations included
- [ ] REST framework permissions set
- [ ] Template context appropriate

**Security:**
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection safe (ORM)
- [ ] XSS prevention (Django templates)
- [ ] CSRF tokens used
- [ ] User authentication/authorization

**Testing:**
- [ ] Tests added for new code
- [ ] Existing tests updated
- [ ] Edge cases covered
- [ ] Test coverage maintained

**Performance:**
- [ ] N+1 query problem avoided
- [ ] Database indexes where needed
- [ ] Caching considered
- [ ] Large files/queries optimized

---

## Part 4: Cursor CLI Review Commands

### Security-focused review
```bash
agent -p "Perform a security review of gastats/views/, focusing on:
1. SQL injection vulnerabilities
2. XSS attack vectors
3. CSRF protection
4. Authentication bypass
5. Authorization checks

Report any findings with severity levels."
```

### Performance review
```bash
agent -p "Analyze gastats/models.py for performance issues:
1. N+1 query patterns
2. Missing indexes
3. Unnecessary database hits
4. Inefficient query patterns

Suggest optimizations with before/after code."
```

### Code consistency review
```bash
agent -p "Review gastats/ for consistency issues:
1. Naming conventions
2. Code organization
3. Import ordering
4. Error handling patterns

Provide a consistency report with examples."
```
