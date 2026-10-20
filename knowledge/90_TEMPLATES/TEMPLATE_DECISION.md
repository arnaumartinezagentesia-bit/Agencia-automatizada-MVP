---
title: <Decisión en una frase>
type: decision
status: PROPOSED            # PROPOSED | ACCEPTED | OBSOLETE  (ACCEPTED solo con aprobación explícita; una decisión no se verifica)
date: YYYY-MM-DD
area: <backend | frontend | persistence | agents | providers | infra | process>
source: <official-docs | observed-in-repo | user-provided | inferred>
related_commit: <hash o rama; "n/a" si no aplica>
related_docs: [<p. ej. docs/ARCHITECTURE.md §X>]
supersedes: []
superseded_by: []         # al pasar a OBSOLETE
tags: []
---

# <Título de la decisión>

> Esta nota complementa a la documentación oficial. No puede contradecirla. Si lo hiciera, debe abrirse una revisión explícita de `docs/` en lugar de aceptar esta nota.

## Contexto
Qué problema o pregunta motiva la decisión.

## Documentación oficial relacionada
Enlaces y sección exacta. Indica si la decisión ya está cubierta por `docs/` (en ese caso no hace falta la nota).

## Opciones consideradas
1. <Opción A>: pros / contras.
2. <Opción B>: pros / contras.

## Decisión
Qué se decide, de forma concreta.

## Consecuencias
Qué implica; qué queda condicionado; qué se descarta.

## Compatibilidad con la documentación oficial
- [ ] No contradice `docs/MVP_SCOPE.md`, `ARCHITECTURE.md`, `DATA_CONTRACTS.md`, `AGENT_SPEC.md`, `UI_SPEC.md` ni `MASTER_DEVELOPMENT_PROMPT.md`.
- Si algún punto choca: describir cuál y proponer la revisión necesaria (no aplicar la decisión hasta aprobarla).

## Aprobación
Mientras esté `PROPOSED`: «Pendiente de aprobación».
Para pasar a `ACCEPTED`: quién aprobó explícitamente, cuándo y dónde consta: <...>
`ACCEPTED` no implica que la decisión se haya demostrado funcionando.
