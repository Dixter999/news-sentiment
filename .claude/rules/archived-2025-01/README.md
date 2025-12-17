# Archived Rules - 2025-01

## Reason for Archival

This news-sentiment project is a **web scraper** for ForexFactory and Reddit posts, not a full-stack web application or cloud-native deployment.

These rules were archived because they are **not relevant** to a scraper project focused on data collection and sentiment analysis.

## Archived Rules

### UI/Frontend Development (Not Needed)
- `ui-development-standards.md` - Bootstrap/Tailwind UI frameworks
- `ui-framework-rules.md` - Component-based UI patterns

### Cloud/Infrastructure (Not Needed)
- `ci-cd-kubernetes-strategy.md` - Kubernetes deployment
- `cloud-security-compliance.md` - AWS/Azure/GCP compliance
- `infrastructure-pipeline.md` - IaC and cloud deployments
- `docker-first-development.md` - Docker-first mandates

### DevOps (Overkill)
- `devops-troubleshooting-playbook.md` - Production incident response
- `database-management-strategy.md` - Multi-environment DB strategy
- `database-pipeline.md` - Complex DB migration pipelines

### AI/ML (Too Specialized)
- `ai-integration-patterns.md` - OpenAI/Gemini integration
- `ai-model-standards.md` - LLM deployment patterns
- `prompt-engineering-standards.md` - Prompt design for AI

### Testing (Too Extensive)
- `test-coverage-requirements.md` - Enterprise-level coverage requirements

### Process/Workflow (Simplified)
- `performance-guidelines.md` - Web app performance (not scraper-focused)
- `development-environments.md` - Docker vs Kubernetes complexity
- `pipeline-mandatory.md` - Too rigid for iterative scraper development
- `definition-of-done.md` - Enterprise checklist (overkill)
- `no-pr-workflow.md` - Integrated into git-strategy.md

## What We Created (Scraper-Specific)

- `scraper-security.md` - API keys, rate limiting, data privacy for scrapers
- `scraper-code-quality.md` - Code patterns specific to web scraping

## What We Kept

**Core Development:**
- TDD enforcement
- Testing standards (simplified)
- Code quality basics
- Git strategy
- GitHub operations

**Project Management:**
- Agent coordination
- Context optimization
- Error handling
- Development workflow

**Scrapers Need:**
- Simple testing
- Error handling
- Data validation
- Git/GitHub for version control
- Basic security (API keys, rate limiting)

## Restoration

If any of these rules become relevant (e.g., you build a web UI for the scraped data), simply move them back to the parent `rules/` directory.
