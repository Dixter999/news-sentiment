---
name: polished-greeting-starling
status: backlog
created: 2025-11-30T10:22:35.813Z
progress: 0%
prd: .claude/prds/polished-greeting-starling.md
github: https://github.com/Dixter999/news-sentiment/issues/2
priority: high
---

# Epic: polished-greeting-starling

## Overview
Build a standalone service in the `news-sentiment` repo to ingest Economic Calendar events via a **Playwright scraper**, score them using **Gemini (LLM)**, and store them in the shared AI Model DB. Th

### Vision
Build a standalone service in the `news-sentiment` repo to ingest Economic Calendar events via a **Playwright scraper**, score them using **Gemini (LLM)**, and store them in the shared AI Model DB. This replaces the previous Selenium/Heuristic approach.

**Goal**: Provide LLM-derived sentiment scores for economic events to improve PPO entry timing.

---


## Architecture Decisions

### Technology Stack
- **Scraper**: Playwright (headless browser automation)
- **Sentiment Analysis**: Google Gemini LLM
- **Database**: PostgreSQL (shared ai_model DB)
- **Language**: Python 3.11+

### Design Patterns
- Pipeline architecture (Scrape → Analyze → Store)
- Test-driven development
- CLI-based orchestration

## Technical Approach

### Workflow
```
Forex Factory Website
        ↓ (Playwright scraper)
Economic Event Data
        ↓ (Gemini LLM)
Sentiment Score (-1.0 to 1.0)
        ↓
PostgreSQL: economic_events table
```

### Key Components
- **ForexFactoryScraper**: Playwright-based calendar scraper
- **SentimentAnalyzer**: Gemini API integration for scoring
- **CLI Orchestrator**: Command-line interface for pipeline control

## Implementation Strategy

### Phase 1: Project Setup (Day 1)
- Create project structure
- Set up pyproject.toml with dependencies
- Configure environment variables
- Install Playwright browser

### Phase 2: Database Layer (Day 1)
- Create migration with sentiment_score and raw_response columns
- Implement SQLAlchemy models
- Set up connection manager

### Phase 3: Playwright Scraper (Day 2)
- Implement ForexFactoryScraper class
- Handle calendar navigation and parsing
- Convert ET → UTC timezone

### Phase 4: Gemini Analyzer (Day 2-3)
- Implement SentimentAnalyzer class
- Design sentiment scoring prompt
- Handle rate limits and errors

### Phase 5: Orchestration & Testing (Day 3-4)
- Implement CLI orchestrator
- Write integration tests
- Create documentation

## Dependencies

### External Dependencies
- playwright>=1.40.0
- google-generativeai>=0.3.0
- sqlalchemy>=2.0.0
- psycopg2-binary>=2.9.9

### Internal Dependencies
- Shared PostgreSQL database (ai_model)
- Trading project (consumes sentiment scores)

## Success Criteria

### This Project
- [ ] Scraper extracts all FF calendar fields correctly
- [ ] Gemini generates meaningful sentiment scores (-1.0 to 1.0)
- [ ] All events stored in `economic_events` table
- [ ] `raw_response` captures LLM reasoning for debugging
- [ ] Test coverage > 80%

### Integration Phase (Trading Project)
- [ ] PPO can query sentiment scores by timestamp
- [ ] Observation space includes sentiment feature
- [ ] No regression in model performance

---

## Estimated Effort

**Total**: 1w 1d

### Breakdown by Type:
- Setup: 2h
- Frontend: 1d
- Backend: 3d
- Integration: 1d
- Testing: 1d
- Deployment: 4h

## Tasks Created

| # | Task | Type | Effort | Parallel | Depends On | GitHub |
|---|------|------|--------|----------|------------|--------|
| 001 | Project Setup and Dependencies | setup | 2h | Yes | - | [#3](https://github.com/Dixter999/news-sentiment/issues/3) |
| 002 | Database Schema and SQLAlchemy Models | database | 3h | No | 001 | [#4](https://github.com/Dixter999/news-sentiment/issues/4) |
| 003 | Implement Playwright Forex Factory Scraper | scraper | 8h | No | 002 | [#5](https://github.com/Dixter999/news-sentiment/issues/5) |
| 004 | Implement Gemini Sentiment Analyzer | analyzer | 8h | Yes | 002 | [#6](https://github.com/Dixter999/news-sentiment/issues/6) |
| 005 | Implement CLI Orchestrator | integration | 4h | No | 003, 004 | [#7](https://github.com/Dixter999/news-sentiment/issues/7) |
| 006 | Write Integration Tests | testing | 6h | Yes | 005 | [#8](https://github.com/Dixter999/news-sentiment/issues/8) |
| 007 | Documentation and README | docs | 3h | Yes | 006 | [#9](https://github.com/Dixter999/news-sentiment/issues/9) |

### Summary
- **Total tasks**: 7
- **Parallel tasks**: 4 (001, 004, 006, 007)
- **Sequential tasks**: 3 (002, 003, 005)
- **Estimated total effort**: 34 hours (~4-5 days)

### Critical Path
```
001 → 002 → 003 ──┐
         ↘ 004 ──┼→ 005 → 006 → 007
```

### Phases Alignment
| Phase | Tasks | Duration |
|-------|-------|----------|
| Phase 1: Project Setup | 001 | 2h |
| Phase 2: Database Layer | 002 | 3h |
| Phase 3: Playwright Scraper | 003 | 8h |
| Phase 4: Gemini Analyzer | 004 | 8h (parallel with 003) |
| Phase 5: Orchestration & Testing | 005, 006, 007 | 13h |

## Notes

- PRD updated 2025-11-30: Changed from Selenium/Heuristics to Playwright/Gemini
- Tasks decomposed following Gemini + Playwright architecture
- All tasks include TDD requirements
- Tasks 003 and 004 can be developed in parallel after database setup

---

*Generated on 2025-11-30T10:22:35.813Z by PM System*
*Tasks decomposed on 2025-11-30T10:22:44Z - Gemini + Playwright architecture*
*Synced to GitHub on 2025-11-30T10:30:00Z - Epic #2, Tasks #3-#9*