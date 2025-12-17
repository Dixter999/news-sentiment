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

### Context Management (Archived 2025-12-17)
- `agent-coordination.md` - Complex multi-agent coordination (17.6k tokens)
- `context7-enforcement.md` - Context7 MCP specific (10.7k tokens)
- `context7-enforcement-optimized.md` - Context7 optimization (5.6k tokens)
- `context-hygiene.md` - Context cleanup patterns (5.2k tokens)
- `context-optimization.md` - Agent context preservation (4.1k tokens)

### Framework Development (Archived 2025-12-17)
- `command-pipelines.md` - PM system command flows (5.5k tokens)
- `framework-path-rules.md` - Framework path conventions (5.3k tokens)
- `use-ast-grep.md` - AST grep integration (4.6k tokens)
- `golden-rules.md` - Generic development rules (4.4k tokens)
- `standard-patterns.md` - Command standard patterns (4.0k tokens)
- `frontmatter-operations.md` - YAML frontmatter handling
- `strip-frontmatter.md` - Frontmatter removal
- `test-execution.md` - Duplicate of testing-standards

## What We Created (Scraper-Specific)

- `scraper-security.md` - API keys, rate limiting, data privacy for scrapers
- `scraper-code-quality.md` - Code patterns specific to web scraping

## What We Kept (Active Rules)

**Core Development:**
- `tdd.enforcement.md` - TDD cycle (RED-GREEN-REFACTOR)
- `testing-standards.md` - Test requirements
- `code-quality-standards.md` - Code quality standards
- `git-strategy.md` - Git workflow
- `github-operations.md` - GitHub CLI operations
- `naming-conventions.md` - Naming standards
- `datetime.md` - Timestamp handling
- `development-workflow.md` - Basic workflow patterns

**Scraper-Specific (Most Important):**
- `scraper-security.md` - API keys, rate limiting, data privacy
- `scraper-code-quality.md` - Scraper-specific patterns

**General Security:**
- `security-checklist.md` - Security requirements

**Agent Management:**
- `agent-mandatory.md` - When to use specialized agents

## Restoration

If any of these rules become relevant (e.g., you build a web UI for the scraped data), simply move them back to the parent `rules/` directory.
