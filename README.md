# Personal Boxing Coach Backend (Schema + Exercise DB v1)

This repository contains the first backend building block for a **single amateur male boxer**:
a strict exercise schema and a practical, evidence-tagged exercise database.

## Scope in v1

This version includes only:

- strict schema validation for boxing exercise records
- starter exercise database (46 exercises)
- deterministic data validation utilities
- test coverage for schema and starter data quality

This version intentionally does **not** include:

- frontend or web app
- chatbot layer
- auth, cloud deployment, or external database servers

## Project structure

- `src/exercise_schema.py` - strict schema fields, controlled vocabularies, and validators
- `src/exercises.json` - starter exercise database (40–50 range satisfied)
- `src/sample_data.py` - loading + validation helper for starter dataset
- `tests/test_exercise_schema.py` - tests for schema and dataset integrity

## Training-design assumptions baked into data

The starter data prioritizes combat-sport transfer:

- lower-body force and explosiveness
- rotational power for punch transfer
- boxing-specific conditioning and technical round structures
- aerobic base support (Zone 2)
- fatigue-cost awareness and fight-week suitability flags
- practical setup across `solo`, `gym`, and `park`

## Quickstart

```bash
python -m pytest -q
python -m src.sample_data
```

## What to build next

Suggested next backend steps (still without UI/chat):

1. Weekly session planner with fatigue budgeting
2. Fight-camp phase rules (general prep, specific prep, taper)
3. Weakness-driven exercise selection logic
4. Session history tracking and trend summaries
