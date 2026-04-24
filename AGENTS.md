# Project instructions

This repo is a personal boxing coach backend for one athlete only.

## Priorities

* Prioritize boxing performance over generic fitness
* Prefer explicit rules over vague AI behavior
* Keep logic inspectable and easy to edit
* Do not build frontend or chat layers unless explicitly requested

## Coding style

* Python only
* Use type hints
* Keep modules small and readable
* Avoid overengineering
* Prefer deterministic logic

## Scope

For now, only work on:

* exercise schema
* exercise database
* validation
* tests

Do not add:

* web app
* frontend
* chatbot wrapper
* database server
* auth
* cloud deployment

## Testing

Whenever modifying schema or exercise data:

* run tests
* make sure required fields are validated
* keep data format consistent
