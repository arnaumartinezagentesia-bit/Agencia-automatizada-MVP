---
title: error.details no debe almacenar la salida cruda del LLM (requisito pendiente para la Fase 7)
type: decision
status: PROPOSED            # pendiente de aprobación; no implementado ni probado
date: 2026-10-23
area: persistence
source: observed-in-repo
related_commit: 5177efd (rama feat/persistence-migrations, cambios de la Fase 3 sin commit)
related_docs: [docs/DATA_CONTRACTS.md §13, docs/DATA_CONTRACTS.md §10, docs/DATA_CONTRACTS.md §15 (LLM output validation), docs/AGENT_SPEC.md §7.2, docs/MASTER_DEVELOPMENT_PROMPT.md §5]
supersedes: []
superseded_by: []
tags: [error-contract, llm, phase-7, pending, security]
---

# error.details no debe almacenar la salida cruda del LLM (requisito pendiente para la Fase 7)

> Esta nota complementa a la documentación oficial. No puede contradecirla. Si lo hiciera, debe abrirse una revisión explícita de `docs/` en lugar de aceptar esta nota.

## Contexto
La auditoría de la Fase 3 (persistencia) identificó un riesgo pendiente: `ErrorDetail.details` (`backend/app/domain/errors.py`) es un `JsonObject | None` sin restricción de contenido, y `AnalysisRun.error` se persiste completo en la columna JSONB `analysis_runs.error` (`backend/app/persistence/mapping.py`, `models.py`). Por tanto, nada impide hoy que un caso de uso guarde en `details` la respuesta cruda de un modelo.

El riesgo no se materializa en la Fase 3: ningún código actual genera errores con salida de un LLM. Los productores de esos errores (`LLM_ERROR`, `ANALYSIS_VALIDATION_ERROR`) llegan con el caso de uso `CreateMarketAnalysis` de la Fase 7. Por eso la decisión corresponde a esa fase y en la Fase 3 no se cambia el contrato del dominio.

## Documentación oficial relacionada
- `docs/DATA_CONTRACTS.md` §13 «Error contract»: los mensajes de error deben ser seguros para presentarse, y en las respuestas de error nunca deben aparecer secretos, credenciales, API keys ni razonamiento privado del modelo.
- `docs/DATA_CONTRACTS.md` §10 «ModelMetadata»: el contrato nunca debe persistir cadenas de razonamiento ocultas ni trazas de razonamiento privado.
- `docs/DATA_CONTRACTS.md` §15 «LLM output validation» y `docs/AGENT_SPEC.md` §7.2: un resultado de LLM no válido produce `analysis.failed` con `ANALYSIS_VALIDATION_ERROR` y nunca se persiste como `MarketAnalysis` correcto.
- `docs/MASTER_DEVELOPMENT_PROMPT.md` §5: la Fase 7 es el caso de uso `CreateMarketAnalysis`.

`docs/` no prohíbe de forma literal guardar la salida cruda en `error.details`. Este requisito concreta las reglas anteriores para el caso del error persistido y no las contradice.

## Opciones consideradas
1. Restringir ya en la Fase 3 el contrato de `details` (esquema cerrado o validador): cambiaría el contrato del dominio fuera de su fase y sin conocer todavía a los productores de errores. Descartada para la Fase 3.
2. Dejar el contrato como está y exigir la separación en los casos de uso de la Fase 7, con pruebas que la comprueben: respeta los contratos actuales y sitúa la responsabilidad donde se generan los errores. Es la opción propuesta.

## Decisión
**Requisito pendiente para la Fase 7** (propuesto, pendiente de aprobación):

- `error.details` no debe utilizarse para almacenar la salida cruda del LLM.
- Los casos de uso que generen errores deben garantizar esa separación.
- Deben añadirse pruebas que comprueben que la salida cruda del modelo no termina persistida en los detalles del error.
- La solución debe respetar los contratos de dominio existentes o, si fuera necesario cambiarlos, plantear explícitamente una decisión funcional (revisión de `docs/DATA_CONTRACTS.md` aprobada por el usuario).
- No debe considerarse resuelto hasta que exista implementación y evidencia de pruebas.

## Consecuencias
- En la Fase 3 no cambia nada: ni el contrato de `ErrorDetail` ni las restricciones SQL.
- En la Fase 7 hay que revisar este requisito antes de implementar los errores `LLM_ERROR` y `ANALYSIS_VALIDATION_ERROR`.
- La evidencia de cumplimiento (tests y commit) se registrará en una nota nueva de tipo `verified-solution`; esta nota no pasa a `VERIFIED`, porque una decisión se aprueba y no se verifica.
- Queda abierto, para la Fase 7, qué contenido seguro y estructurado puede llevar `details` (p. ej., campo afectado o código de validación) en lugar de texto del modelo.

## Compatibilidad con la documentación oficial
- [x] No contradice `docs/MVP_SCOPE.md`, `ARCHITECTURE.md`, `DATA_CONTRACTS.md`, `AGENT_SPEC.md`, `UI_SPEC.md` ni `MASTER_DEVELOPMENT_PROMPT.md` (revisión de las secciones citadas el 2026-10-23).
- Si la Fase 7 necesitara cambiar el contrato de `details`, debe proponerse como revisión explícita de `docs/DATA_CONTRACTS.md`, no resolverse desde esta nota.

## Aprobación
Pendiente de aprobación.
Estado de implementación: no implementado, sin pruebas.
