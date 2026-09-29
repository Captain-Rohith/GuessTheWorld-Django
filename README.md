# GuessTheWorld

A structured Wordle-style deduction platform built with Django. Designed for players who respect five-letter constraints and administrators who appreciate clean audit trails.

> **Note on the title**: Yes, it is *GuessTheWorld*, not *GuessTheWord*. Calling a 5-letter word game by a 4-letter word (`W-O-R-D`) would violate the core invariant. `W-O-R-L-D` fits the grid.

---

## Overview

GuessTheWorld brings the classic word deduction game into a multi-user web architecture with role separation, daily attempt quotas, and real-time evaluation.

### Features

- **Deduction Engine**: 5-letter, 5-attempt grid with authentic two-pass tile evaluation (exact matches, bounded misplaced occurrences, and exclusions) paired with live virtual keyboard tracking.
- **Daily Discipline**: Strict cap of 3 completed sessions per player per calendar day.
- **Admin Telemetry**: Real-time dashboards for player accuracy, daily engagement volume, session breakdowns, and active word pool curation.
- **Role Isolation**: Strict separation between `ADMIN` and `PLAYER` privileges with hardened credential validation rules.

---

## Pre-configured Credentials

| Role | Username | Password | Scope |
| :--- | :--- | :--- | :--- |
| **Admin** | `AdminUser` | `AdminPassword1$` | Analytics, user reports, and word pool management |
| **Player** | `PlayerOne` | `PlayerPassword1%` | Player dashboard and game sessions |

*Self-registration is open for players at `/register/` requiring mixed-case alphanumeric strings and designated symbols (`$`, `%`, `*`, `&`).*

---

## Quickstart

### 1. Setup Database
Initial seed data (words and default accounts) is provisioned automatically upon migration.

```bash
python manage.py migrate
```

### 2. Launch Development Server

```bash
python manage.py runserver
```

Access the application at `http://127.0.0.1:8000/`.

---

## Test Suite

Run the full automated test suite covering game engine logic, quota rules, and admin permissions:

```bash
python manage.py test
```
