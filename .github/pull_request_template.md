## Description
[Description of changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring

## Checklist
- [ ] Code follows style guidelines (PEP 8)
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Pre-commit checks passed (`pre-commit run --all-files`)
- [ ] No hardcoded secrets
- [ ] AI code review completed (see below)

## Review Checklist

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

## Cursor CLI Review Summary

**Command Used:**
```bash
agent -p "Review [files/specify scope] for..."
```

**AI Findings:**
[Paste key AI review findings here]

**Action Items:**
- [ ] [Item 1]
- [ ] [Item 2]

## Review Notes
[Any notes for reviewers]

## Screenshots (if applicable)
[Paste screenshots here]

## Related Issues
Closes #[issue-number]

## Testing
[Describe how you tested these changes]
