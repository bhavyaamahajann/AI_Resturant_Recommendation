# Project Context

> **Source:** [`docs/problemstatement.txt`](./problemstatement.txt)  
> **Generated:** 2026-05-17  
> **Purpose:** Authoritative brief for agents and developers building the AI-powered restaurant recommendation system.

---

## Summary

Build an **AI-powered restaurant recommendation service** inspired by Zomato. The application combines **structured restaurant data** from a real-world dataset with a **Large Language Model (LLM)** to produce personalized, human-like recommendations from user preferences (location, budget, cuisine, ratings, and more).

---

## Problem

Users need restaurant suggestions that match their preferences—not just raw filtered lists, but **ranked, explained recommendations** that feel thoughtful and actionable. The system must bridge structured data (names, locations, cuisines, costs, ratings) and natural-language reasoning via an LLM.

---

## Objectives

Design and implement an application that:

1. **Accepts user preferences** — location, budget, cuisine, minimum rating, and optional extras (e.g., family-friendly, quick service).
2. **Uses a real-world restaurant dataset** — the Zomato dataset on Hugging Face.
3. **Leverages an LLM** — to rank options, explain fit, and optionally summarize choices.
4. **Displays clear, useful results** — top picks with key fields and AI-generated explanations.

---

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face:  
  **https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation**
- Extract relevant fields: restaurant name, location, cuisine, cost, rating, and related attributes.

### 2. User Input

Collect preferences:

| Input | Examples |
|-------|----------|
| Location | Delhi, Bangalore |
| Budget | low, medium, high |
| Cuisine | Italian, Chinese |
| Minimum rating | numeric threshold |
| Additional preferences | family-friendly, quick service |

### 3. Integration Layer

- Filter and prepare restaurant records matching user input.
- Pass structured candidate results into an LLM prompt.
- Design prompts so the LLM can **reason** and **rank** options effectively.

### 4. Recommendation Engine (LLM)

The LLM should:

- **Rank** restaurants by fit to preferences.
- **Explain** why each recommendation matches the user.
- **Optionally summarize** the overall set of choices.

### 5. Output Display

Present top recommendations in a user-friendly format:

- Restaurant name  
- Cuisine  
- Rating  
- Estimated cost  
- AI-generated explanation  

---

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Load and preprocess Zomato dataset from Hugging Face | High |
| FR-2 | Extract fields: name, location, cuisine, cost, rating, etc. | High |
| FR-3 | Collect user preferences (location, budget, cuisine, min rating, extras) | High |
| FR-4 | Filter dataset by user criteria before LLM call | High |
| FR-5 | Build LLM prompt with structured candidate data | High |
| FR-6 | LLM ranks restaurants and generates per-item explanations | High |
| FR-7 | Optional LLM summary of recommendation set | Medium |
| FR-8 | Display top N results with name, cuisine, rating, cost, explanation | High |

---

## Data & Integrations

| Resource | Role |
|----------|------|
| [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) | Primary restaurant dataset |
| LLM API | Ranking, reasoning, explanations, optional summary |

**Key dataset fields (expected):** restaurant name, location, cuisine, cost, rating.

---

## Architecture (Logical)

```
User Preferences → Filter/Prepare Data → LLM Prompt → Rank + Explain → UI Output
        ↑                    ↑
   Hugging Face         Structured
   Zomato Dataset       candidate list
```

---

## Constraints & Assumptions

- Recommendations are grounded in **filtered dataset rows** passed to the LLM—not purely hallucinated venues.
- Budget is expressed as **low / medium / high** (mapping to cost fields may be required during preprocessing).
- Location and cuisine matching depend on dataset field quality and normalization.
- LLM choice, API keys, and hosting are implementation decisions not specified in the problem statement.

---

## Success Criteria

- User can enter preferences and receive **top recommendations** with required fields displayed.
- Recommendations are **personalized** to stated location, budget, cuisine, and rating constraints.
- Each recommendation includes a **clear AI-generated explanation** of why it fits.
- End-to-end flow works: **ingest data → input → filter → LLM → display**.

---

## Out of Scope (Implicit)

Not defined in the problem statement; clarify if needed:

- User accounts, auth, or saved history  
- Real-time availability, reservations, or maps  
- Mobile-native apps (web UI is sufficient unless specified elsewhere)  
- Training a custom model (use existing LLM via API)

---

## Open Questions

- Exact schema and column names in the Hugging Face dataset  
- How to map **budget tiers** (low/medium/high) to numeric cost fields  
- Target UI stack (CLI, web app, API-only)  
- Which LLM provider and model to use  
- Number of top recommendations to show (N)

---

## Related Artifacts

| File | Purpose |
|------|---------|
| `docs/problemstatement.txt` | Original problem statement |
| `docs/context.md` | This file — structured context for implementation |
