---
title: Índice de la memoria del proyecto
status: PROPOSED
date: 2026-10-20
area: knowledge
tags: [index]
---

# Índice

Punto de entrada de la memoria. Léelo antes de empezar cualquier tarea. Guía completa en [`../README.md`](../README.md).

## Antes de trabajar

1. Lee la documentación oficial aplicable a la tarea (`docs/`, jerarquía en el README).
2. Busca aquí notas relevantes: [[#Decisiones]], [[#Soluciones verificadas]], [[#Incidentes]], [[#Experimentos]].
3. Si hay conflicto entre una nota y `docs/`, prevalece `docs/`.
4. Una nota `PROPOSED` u `OBSOLETE`, o cualquier hipótesis (`type: experiment`), **no es un hecho**. Solo `VERIFIED` indica respaldo por evidencia y solo `ACCEPTED` indica aprobación explícita. Ver [Tipos y estados](../README.md#tipos-y-estados).

## Documentación oficial (fuente de verdad, fuera de `knowledge/`)

Orden de autoridad:

1. [MVP_SCOPE](../../docs/MVP_SCOPE.md): qué está permitido.
2. [ARCHITECTURE](../../docs/ARCHITECTURE.md): capas e interfaces.
3. [DATA_CONTRACTS](../../docs/DATA_CONTRACTS.md): esquemas exactos.
4. [AGENT_SPEC](../../docs/AGENT_SPEC.md): comportamiento del agente.
5. [UI_SPEC](../../docs/UI_SPEC.md): frontend.
6. [MASTER_DEVELOPMENT_PROMPT](../../docs/MASTER_DEVELOPMENT_PROMPT.md): protocolo de implementación y fases.

## Notas

Añade cada nota nueva en su sección, con enlace (wikilink), estado y una línea de resumen.

### Decisiones
- [[2026-10-23_error-details-sin-salida-cruda-del-llm]] — `PROPOSED`, pendiente para la Fase 7: `error.details` no debe almacenar la salida cruda del LLM; sin implementar ni probar.

### Soluciones verificadas
_Ninguna todavía._

### Incidentes
- [[2026-10-22-alembic-naming-convention-duplicated-prefix]] — `PROPOSED`, resuelto: prefijo `ck_` duplicado en migraciones con `naming_convention`.
- [[2026-10-22-contextmanager-keeps-original-exception-as-context]] — `PROPOSED`, resuelto: `__context__` conserva la excepción SQL original.

### Experimentos
_Ninguno todavía._

### Playbooks
_Ninguno todavía._

### Changelog
- [[2026-10-23_alta-decision-error-details-sin-salida-cruda-del-llm]] — `PROPOSED`, alta de la decisión pendiente para la Fase 7 sobre `error.details`.

Ver [`../06_CHANGELOG/`](../06_CHANGELOG/).

## Plantillas

- [[TEMPLATE_DECISION]]
- [[TEMPLATE_VERIFIED_SOLUTION]]
- [[TEMPLATE_INCIDENT]]
- [[TEMPLATE_EXPERIMENT]]
- [[TEMPLATE_CHANGELOG_ENTRY]]

## Abrir en Obsidian

1. Obsidian → *Open folder as vault* → selecciona la **raíz del repositorio** (la carpeta que contiene `.git`, `docs/` y `knowledge/`), no `knowledge/`.
2. Abre este archivo: `knowledge/00_START_HERE/INDEX.md`.
3. Si Obsidian avisa de «Restricted mode», déjalo activo: no hacen falta plugins.
4. Obsidian creará `.obsidian/` en la raíz; está ignorado por Git.
