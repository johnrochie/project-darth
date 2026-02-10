# GitHub Actions CI/CD Setup - GAA Stats App

## Overview
Complete GitHub Actions workflow for testing the GAA Stats App backend with PostgreSQL service, pytest, and coverage reporting.

## Files Created

### 1. `.github/workflows/test.yml`
- Triggers on every push and pull request
- Uses Ubuntu latest runner
- Python 3.12 environment
- PostgreSQL 16 service with health checks
- Caches pip dependencies for faster runs
- Runs pytest with coverage reporting
- Uploads coverage artifacts (retained for 30 days)

### 2. `backend/pytest.ini`
- Configures pytest for Django
- Sets Django settings module
- Configures test paths and markers
- Enables asyncio support
- Warning filters for cleaner output

## Workflow Configuration

### Environment Variables Set in CI
- `SECRET_KEY`: Test secret key
- `DEBUG`: True
- `DB_NAME`: test_gaastats
- `DB_USER`: postgres
- `DB_PASSWORD`: postgres
- `DB_HOST`: localhost
- `DB_PORT`: 5432
- `REDIS_URL`: redis://localhost:6379/0

### Test Command
```bash
pytest --cov=gaastats --cov-report=xml --cov-report=term-missing
```

### PostgreSQL Service
- Uses postgres:16 image
- Database: test_gaastats
- Health check ensures database is ready before tests run

## YAML Syntax Validation
✅ Workflow YAML syntax is verified and valid

## How to Push to GitHub

### Step 1: Verify Files Are Created
```bash
cd /home/jr/.openclaw/workspace/projects/gaastats-app
ls -la .github/workflows/
ls -la backend/pytest.ini
```

### Step 2: Add Files to Git
```bash
git add .github/workflows/test.yml
git add backend/pytest.ini
```

### Step 3: Commit Changes
```bash
git commit -m "Add GitHub Actions CI/CD workflow with pytest and coverage reporting"
```

### Step 4: Add GitHub Remote (if not already configured)
```bash
# Replace YOUR_GITHUB_USERNAME with your actual username
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/gaastats-app.git
```

### Step 5: Push to GitHub
```bash
# First push (if remote already exists)
git push -u origin master

# Or if the remote doesn't exist and you just added it:
git push -u origin master
```

### Step 6: Trigger the Workflow
The workflow will automatically run on:
- Every push to any branch
- Every pull request to any branch

### Alternative Force Push (if needed)
```bash
git push -f origin master
```

## View Workflow Results

After pushing:
1. Go to your GitHub repository
2. Click on the "Actions" tab
3. You'll see the "GAA Stats App Tests" workflow running
4. Click on the workflow run to view:
   - Test results
   - Coverage reports
   - Logs from each step

## Download Coverage Artifacts

To download the coverage report:
1. Go to the Actions tab
2. Click on the completed workflow run
3. Scroll to "Artifacts" at the bottom
4. Click "coverage-report" to download the XML file

## Next Steps

After the workflow is running successfully, consider adding:

### Coverage Badge (Optional)
Add this to your README.md:
```markdown
![Coverage](https://img.shields.io/badge/coverage-%??%20-success)
```

### Integration with Codecov (Optional)
To integrate with Codecov for better coverage visualization:

1. Sign up at codecov.io
2. Add the codecov uploader to your workflow:
```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    files: ./backend/coverage.xml
    fail_ci_if_error: false
```

## Troubleshooting

### If Tests Fail on CI
1. Check the Logs tab in Actions
2. Ensure all environment variables are set correctly
3. Verify PostgreSQL service is healthy
4. Check that all dependencies are in requirements.txt

### If Coverage Report is Missing
1. Ensure pytest-cov is in requirements.txt (it is!)
2. Check the "Upload coverage report" step logs
3. Verify the working-directory is set correctly

### If Database Connection Fails
1. Verify PostgreSQL service health checks are passing
2. Check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, and DB_NAME
3. Ensure the workflow waits for postgres to be ready before running tests

## Summary

✅ `.github/workflows/test.yml` - Complete CI/CD workflow
✅ `backend/pytest.ini` - Pytest configuration for Django
✅ YAML syntax validated
✅ PostgreSQL 16 service configured
✅ Coverage reporting enabled
✅ Pip caching configured
✅ Artifacts upload configured

Ready to push to GitHub and trigger the first workflow run!
