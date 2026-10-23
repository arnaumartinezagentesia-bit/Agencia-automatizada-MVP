---
title: Un @contextmanager que traduce excepciones conserva la original como __context__
type: incident
status: PROPOSED
lifecycle: resolved
date: 2026-10-22
resolved_on: 2026-10-22
area: persistence
severity: medium
source: command-output
related_commit: 5177efd (rama feat/persistence-migrations, cambios sin commit)
related_docs: []
related_solution: []
tags: [python, exceptions, security, sqlalchemy]
---

# Un @contextmanager que traduce excepciones conserva la original como __context__

## Síntoma
`AnalysisRunRepository._scope` (generador con `@contextmanager`) capturaba `SQLAlchemyError` y lanzaba `PersistenceError` sin el mensaje original, pero `PersistenceError.__context__` seguía siendo la excepción de SQLAlchemy, que contiene la sentencia y los parámetros (el JSON de la fila).

## Contexto
Fase 3. Un test unitario comprobaba `__context__ is None`, pero forzaba el error en `session.begin()` (antes del `yield`), no desde el cuerpo del `with`, y por eso pasaba.

## Cómo reproducir
Un contextmanager con la misma forma que `_scope`, y un cuerpo `with repo._scope(None): raise OperationalError(...)`. Salida observada: `PersistenceError context: OperationalError`.

## Causa
- **Confirmada** (observada): al lanzar la excepción desde el cuerpo del `with`, la nueva excepción lleva la original como `__context__`.
- **Sospechada** (no comprobada en el código fuente de contextlib): que `contextlib` invoque `gen.throw()` mientras la original sigue "en tratamiento".

## Evidencia de la causa
Script de reproducción (salida arriba) y revisión independiente que lo reprodujo con `KeyError`. Tras el cambio, los tests `test_errors_raised_by_the_work_*` y `test_creating_the_same_run_twice_*` comprueban `__context__ is None`.

## Resolución
La traducción pasa a una función normal `_run(session, work)`, que captura en el `except` y lanza fuera del manejador. Sin nota de solución verificada todavía.

## Prevención
Los tests anteriores fuerzan el error desde dentro del trabajo, no solo al abrir la transacción.

## Documentación oficial relacionada
Ninguna contradicción con `docs/`.
