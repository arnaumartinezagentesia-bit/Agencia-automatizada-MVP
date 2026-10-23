---
title: Alembic duplica el prefijo de los CHECK cuando la migración ya trae el nombre completo
type: incident
status: PROPOSED
lifecycle: resolved
date: 2026-10-22
resolved_on: 2026-10-22
area: persistence
severity: low
source: test-output
related_commit: 5177efd (rama feat/persistence-migrations, cambios sin commit)
related_docs: [ARCHITECTURE §21]
related_solution: []
tags: [alembic, sqlalchemy, naming-convention, postgres]
---

# Alembic duplica el prefijo de los CHECK cuando la migración ya trae el nombre completo

## Síntoma
En PostgreSQL, las constraints CHECK creadas por la migración inicial se llamaban `ck_analysis_runs_ck_analysis_runs_status_valid` en lugar de `ck_analysis_runs_status_valid`. `alembic check` no lo detecta (Alembic no compara CHECK).

## Contexto
Fase 3. `Base.metadata` define `naming_convention` con `"ck": "ck_%(table_name)s_%(constraint_name)s"`. La migración pasaba el nombre ya completo: `sa.CheckConstraint(..., name="ck_analysis_runs_status_valid")`.

## Cómo reproducir
1. `env.py` con `target_metadata = Base.metadata` y la convención anterior.
2. Migración con `name="ck_<tabla>_<algo>"` en `op.create_table`.
3. `alembic upgrade head` y consultar `pg_constraint.conname`.

## Causa
- **Confirmada** (observada): pasando el nombre completo, la base queda con el prefijo duplicado; pasándolo con `op.f(...)`, queda correcto.
- **Sospechada** (no comprobada en el código fuente): que Alembic trate el nombre recibido como `constraint_name` y le aplique la convención.

## Evidencia de la causa
Test `tests/integration/test_migrations.py::test_check_constraint_names_match_the_models` contra PostgreSQL 18.6 con `alembic==1.20.0` y `sqlalchemy==2.1.6`. Antes del cambio falló con elementos extra como `ck_analysis_runs_ck_analysis_runs_started_after_created`; tras el cambio pasa (la suite de integración completa: 102 passed).

## Resolución
Envolver los nombres de la migración con `op.f("ck_analysis_runs_...")`, que marca el nombre como definitivo y evita aplicar la convención. Sin nota de solución verificada todavía (queda a criterio de revisión).

## Prevención
El test anterior compara los nombres de CHECK de la base con los de los modelos.

## Documentación oficial relacionada
Ninguna contradicción con `docs/`.
