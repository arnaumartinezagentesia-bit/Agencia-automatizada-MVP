---
title: Alta de la decisión propuesta para la Fase 7 sobre error.details y la salida cruda del LLM
type: changelog
status: PROPOSED
date: 2026-10-23
change_kind: added
area: knowledge
source: user-provided
related_commit: 5177efd (rama feat/persistence-migrations, cambios de la Fase 3 sin commit)
affected_notes: ["[[2026-10-23_error-details-sin-salida-cruda-del-llm]]"]
related_docs: [docs/DATA_CONTRACTS.md §13, docs/MASTER_DEVELOPMENT_PROMPT.md §5]
tags: [error-contract, llm, phase-7, pending]
---

# Alta de la decisión propuesta para la Fase 7 sobre error.details y la salida cruda del LLM

## Qué cambió
Se añadió la nota [[2026-10-23_error-details-sin-salida-cruda-del-llm]] (`type: decision`, `status: PROPOSED`). Propone, para la Fase 7, impedir que `error.details` almacene la salida cruda del LLM y exigir pruebas que acrediten esa separación. Se enlazó desde [[INDEX]].

La decisión sigue en `PROPOSED`: no está aprobada, implementada ni probada.

## Por qué
La auditoría de la Fase 3 detectó que `ErrorDetail.details` admite cualquier objeto JSON y se persiste en `analysis_runs.error`. La decisión corresponde a la Fase 7, cuando se implementen los casos de uso que generan esos errores. Por eso se registra como requisito pendiente sin cambiar el contrato del dominio en la Fase 3.

## Evidencia
Esta entrada registra el alta de una propuesta. No contiene evidencia de que el requisito se cumpla, porque todavía no hay implementación.

Contexto de la ejecución de verificación de la Fase 3 del 2026-10-23, con coverage.py 7.17.0 (`--source=app --branch`), pytest 9.1.1 y Python 3.14.7. Estas cifras describen esa ejecución concreta, no son una garantía general de calidad y no responden a ningún umbral mínimo:

- 667 pruebas unitarias aprobadas.
- 108 pruebas de integración aprobadas contra PostgreSQL real (`agencia_automatizada_test`, 127.0.0.1:54329).
- 775 pruebas aprobadas en la suite combinada.
- Suite combinada: cobertura de sentencias del 98,8 %, cobertura de ramas del 97,0 % y cobertura combinada del 98,5 % según coverage.py.

Ninguna de estas pruebas comprueba el requisito sobre `error.details`.

## Impacto
- Antes de implementar `LLM_ERROR` y `ANALYSIS_VALIDATION_ERROR` en la Fase 7, hay que revisar la decisión y que el usuario la apruebe o la descarte.
- La decisión no puede pasar a `ACCEPTED` sin aprobación explícita del usuario. La evidencia de su cumplimiento (implementación y pruebas) se registrará en una nota nueva.
- No se plantea ninguna revisión de `docs/`. Si la Fase 7 necesitara cambiar el contrato de `details`, deberá proponerse explícitamente.
