# AI usage

> Edit this file so it reflects what you actually did. Delete anything that is not true.

## Where AI was used
- Claude generated the first version of the FastAPI backend (`rules.py`, `store.py`, `main.py`), the React frontend, the sample `seed.json`, unit tests and the README draft.

## What I accepted
- (fill in: e.g. rule engine structure, JSON-file persistence with atomic writes, endpoint layout)

## What I changed
- (fill in: e.g. anything you edited after reading the code, assumptions you reworded or added)

## What I rejected
- (fill in: e.g. suggestions or approaches you dropped)

## How I verified
- Ran `pytest` for the rule engine (overlap, 11h boundary, 40h boundary, week boundary, certification, own-shift).
- (fill in: manual flows you tried in the UI: post, claim, refuse, approve with re-check failure, restart persistence)
