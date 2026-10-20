---
title: <Hipótesis o experimento en una frase>
type: experiment
status: PROPOSED           # PROPOSED | ACCEPTED | OBSOLETE  (un experimento nunca es VERIFIED: se promueve)
stage: hypothesis          # hypothesis | running | concluded  (ciclo de vida; no es un estado de conocimiento)
outcome:                   # solo si stage = concluded: confirmed | refuted | inconclusive
superseded_by: []          # al pasar a OBSOLETE
date: YYYY-MM-DD
area: <backend | frontend | persistence | agents | providers | infra | process>
source: <inferred | external-docs | observed-in-repo | user-provided>
related_commit: <hash/rama sobre la que se ejecuta>
related_docs: []
promoted_to: []            # nota creada en 01_DECISIONS o 02_VERIFIED_SOLUTIONS si se confirma
tags: []
---

# <Título>

> **Esto es una hipótesis / experimento, no un hecho.** Nada de lo que aquí se afirma debe usarse como verdad establecida hasta que se promueva a una solución verificada o a una decisión aprobada.

## Hipótesis
Afirmación contrastable.

## Motivación
Por qué se plantea y qué evidencia previa (si la hay) la sugiere.

## Método
Qué se hará para contrastarla y en qué entorno.

## Criterio de éxito / fallo
Definido **antes** de ejecutar.

## Resultados
Datos observados (comando, salida saneada, métricas). Vacío mientras `stage: hypothesis`.

## Conclusión
Qué se concluye, con qué grado de confianza y límites.

## Siguiente paso
- Si `outcome: confirmed`: crear nota nueva en `02_VERIFIED_SOLUTIONS/` (con su propia evidencia) o `01_DECISIONS/`, y enlazarla en `promoted_to`.
- Si `refuted` / `inconclusive`: indicar qué se descarta o qué falta.

## Documentación oficial relacionada
Enlaces. Un experimento nunca modifica `docs/`; si apunta a un cambio, proponer revisión explícita.
