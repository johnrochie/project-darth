# AI Code Review Workflow Guide

**Date:** 2026-02-10 11:05 UTC
**Phase:** Testing Foundation - Phase 4

---

## Quick Start

### Step 1: Install Pre-commit Hooks

```bash
cd /home/jr/.openclaw/workspace/projects/gaastats-app
pip install pre-commit
pre-commit install
```

### Step 2: Run Pre-commit Checks Manually

```bash
# Check all files
pre-commit run --all-files

# Check only staged files
pre-commit run

# Fix auto-fixable issues
pre-commit run --fix
```

### Step 3: AI Code Review with Cursor

```bash
# Review specific file
agent -p "Review gaastats/views/api_urls.py for code quality, security, and Django best practices."

# Review entire module
agent -p "Review gaastats/models.py for:
1. Code readability
2. Security vulnerabilities
3. Performance issues
4. Django best practices
5. Test coverage gaps"

# Security-focused review
agent -p "Perform security audit on gastats/views/ for:
1. SQL injection risks
2. XSS vulnerabilities
3. Authentication/authorization issues
4. Hardcoded secrets"
```

---

## Daily Workflow

### Before Committing

```bash
# 1. Stage your changes
git add .

# 2. Run pre-commit hooks
pre-commit run

# 3. Fix any issues
pre-commit run --fix

# 4. Run AI review on changed files
git diff --cached --name-only | grep '\.py$' | grep -E '^(gaastats|tests)/' | while read file; do
  echo "=== AI Review: $file ==="
  agent -p "Quick review of $file. Focus on bugs, security, and obvious issues."
done

# 5. Commit
git commit
```

### Pull Request Workflow

1. **Create feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make changes and review**
```bash
# After code changes
pre-commit run --all-files

# AI review of changes
git diff main --name-only | grep '\.py$' | while read file; do
  agent -p "Review $file for production readiness."
done

# Commit with AI-generated message
agent -p "Generate a conventional commit message for:
$(git diff --cached --stat)"
```

3. **Create PR with AI review summary**
```bash
# Document AI review findings in PR description
# Use .github/pull_request_template.md
```

---

## Review Types

### 1. Quick Review (5 minutes)
**Use for:** Small changes, bug fixes, routine updates

```bash
agent -p "Quick review of gastats/models.py. Focus on obvious bugs and style issues."
```

### 2. Comprehensive Review (15-30 minutes)
**Use for:** New features, core modules, security changes

```bash
agent -p "Comprehensive review of gastats/views/:
1. Code quality and readability
2. Security vulnerabilities
3. Django best practices
4. Performance optimization
5. Test coverage
6. Documentation"

Include recommendations with code examples.
```

### 3. Security Audit (20-40 minutes)
**Use for:** Authentication, authorization, data handling changes

```bash
agent -p "Security audit of gastats/:
1. SQL injection risks
2. XSS vulnerabilities
3. CSRF protection
4. Authentication bypass
5. Authorization flaws
6. Sensitive data exposure

For each finding, provide:
- Severity level
- Exploit scenario
- Fix with code example"
```

### 4. Performance Analysis (15-30 minutes)
**Use for:** Database queries, large data processing, API endpoints

```bash
agent -p "Performance analysis of gastats/:
1. N+1 query problems
2. Missing database indexes
3. Inefficient query patterns
4. Unnecessary database hits
5. Memory leaks

Provide before/after code examples."
```

---

## AI Review Templates

### New Feature Template
```bash
agent -p "Review this new feature [describe feature]:
1. Does it follow Django best practices?
2. Are there security concerns?
3. Is the code testable?
4. What tests should be added?
5. Is performance acceptable?
6. Any edge cases not handled?

Provide specific feedback with code examples."
```

### Bug Fix Template
```bash
agent -p "Review this bug fix:
1. Does the fix address the root cause?
2. Are there unintended side effects?
3. Should we add tests to prevent regression?
4. Is the fix robust?

Provide code review with suggestions."
```

### Refactoring Template
```bash
agent -p "Review this refactoring:
1. Is the code more readable now?
2. Is performance improved or maintained?
3. Are there bugs introduced?
4. Does it follow DRY principles?

Provide review metrics before/after."
```

---

## Cursor CLI Advanced Usage

### Interactive Review Session

```bash
agent  # Start interactive session
# Then use context selection:
@gastats/views/api_urls.py
@gastats/models.py

# Review prompt:
Review these files for consistency and security. Pay attention to:
- Input validation
- Error handling
- Permission checks
- Query patterns
```

### Batch File Review

```bash
# Review all views
find gaastats/views/ -name "*.py" -exec agent -p "Review {} for production readiness" \;

# Review all models
agent -p "Review all Django models in gaastats/models.py for:
1. Proper use of relationships
2. Indexing strategy
3. Security (to_python, from_db)
4. Model methods and properties"
```

### Git Integration

```bash
# Review since last commit
agent -p "Review changes since last commit:
$(git diff HEAD^ --stat)

Focus on breaking changes and security issues."

# Compare branches
agent -p "Compare this branch with main:
$(git diff main --stat)

Report:
1. Breaking changes
2. New dependencies
3. Database migrations needed
4. Performance impact"
```

---

## Review Report Format

### When Reporting Findings

Include:
1. **Issue Title** - Clear description
2. **Severity** - Critical/High/Medium/Low
3. **Location** - File and line number
4. **Description** - What's wrong and why
5. **Code Example** - Current code (if relevant)
6. **Fix Suggestion** - Code or explanation
7. **Testing** - How to verify the fix

### Example Report Format

```markdown
## Finding: SQL Injection Vulnerability

**Severity:** High
**Location:** `gaastats/views/api_views.py:45`

**Description:**
The user input is directly interpolated into a SQL query, allowing SQL injection attacks.

**Current Code:**
```python
query = f"SELECT * FROM players WHERE name = '{name}'"
```

**Fix Suggestion:**
```python
query = "SELECT * FROM players WHERE name = %s"
Player.objects.raw(query, [name])
```

**Testing:**
Test with malicious input: `"name='; DROP TABLE players; --"`
Should safely escape the input instead of executing DROP.
```

---

## Resources

- **Cursor CLI Docs:** https://cursor.com/docs
- **Pre-commit Hooks:** https://pre-commit.com/
- **Bandit Security:** https://bandit.readthedocs.io/
- **Flake8 Linting:** https://flake8.pycqa.org/

---

**Last Updated:** 2026-02-10 11:05 UTC
