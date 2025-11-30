---
issue: 6
title: Project Setup and Dependencies
analyzed: 2025-11-30T10:38:58Z
estimated_hours: 2
parallelization_factor: 2.5
---

# Parallel Work Analysis: Issue #6

## Overview
Create the project structure, configure `pyproject.toml` with Playwright and Gemini dependencies, create `.env.example`, set up the Python development environment, and install Playwright browser. This is the foundation task - no dependencies.

## Parallel Streams

### Stream A: Project Structure and Configuration
**Scope**: Directory structure, pyproject.toml, environment files
**Files**:
- `src/__init__.py`
- `src/main.py` (stub)
- `src/scraper/__init__.py`
- `src/scraper/ff_scraper.py` (stub)
- `src/analyzer/__init__.py`
- `src/analyzer/gemini.py` (stub)
- `src/database/__init__.py`
- `src/database/config.py`
- `src/database/connection.py`
- `src/database/models.py` (stub)
- `pyproject.toml`
- `.env.example`
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 1
**Dependencies**: none

### Stream B: Test Infrastructure
**Scope**: Test directory setup, conftest, initial test files
**Files**:
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_imports.py`
**Agent Type**: python-backend-engineer
**Can Start**: immediately
**Estimated Hours**: 0.5
**Dependencies**: none

### Stream C: Environment Setup and Validation
**Scope**: Virtual environment, pip install, playwright install, validation
**Files**:
- `.venv/` (created)
- Playwright browser binaries
**Agent Type**: bash-scripting-expert
**Can Start**: after Stream A completes
**Estimated Hours**: 0.5
**Dependencies**: Stream A (needs pyproject.toml)

## Coordination Points

### Shared Files
- `pyproject.toml` - Only Stream A modifies this
- No file conflicts expected between streams

### Sequential Requirements
1. Stream A (project structure) before Stream C (environment setup)
2. Stream B can run in parallel with both A and C
3. Final validation requires all streams complete

## Conflict Risk Assessment
- **Low Risk**: Streams work on completely separate file sets
- Stream A: Python source files and config
- Stream B: Test files only
- Stream C: Virtual environment and binaries (no source files)

## Parallelization Strategy

**Recommended Approach**: Parallel with final validation

```
Stream A (Structure) ──────────────┐
                                    ├── Stream C (Environment) ──> Validation
Stream B (Tests) ──────────────────┘
```

1. Launch Stream A and Stream B simultaneously
2. When Stream A completes, start Stream C
3. Stream B can continue in parallel with Stream C
4. Final validation when all complete

## Expected Timeline

With parallel execution:
- Wall time: 1.5 hours
- Total work: 2 hours
- Efficiency gain: 25%

Without parallel execution:
- Wall time: 2 hours

## Pre-existing Code Status

Files that already exist (from initial commit):
- `src/news_sentiment/database/` - Exists with some files
- `pyproject.toml` - Exists but may need updates
- `.env.example` - Exists
- `migrations/` - Exists

**Action**:
1. Review existing `pyproject.toml` for completeness
2. Verify existing database files match PRD structure
3. Restructure if needed (PRD expects `src/` not `src/news_sentiment/`)

## Notes

- This is Task 001 - the foundation for all other tasks
- Playwright browser installation may take time (~100MB download)
- Consider running in Docker for reproducibility
- The existing project structure uses `src/news_sentiment/` but PRD shows `src/` - clarify with stakeholder
- Some files already exist from initial setup - focus on gaps and updates

## Validation Checklist

After completion, verify:
```bash
# 1. Virtual environment works
source .venv/bin/activate

# 2. Package installs
pip install -e ".[dev]"

# 3. Playwright browser installed
playwright install chromium

# 4. Imports work
python -c "from src import main"

# 5. Tests run
pytest tests/ -v

# 6. Linters pass
black --check src/ tests/
ruff check src/ tests/
```
