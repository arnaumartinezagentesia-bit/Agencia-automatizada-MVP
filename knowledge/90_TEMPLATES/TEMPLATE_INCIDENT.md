---
title: <Incidente en una frase>
type: incident
status: PROPOSED           # PROPOSED | ACCEPTED | VERIFIED | OBSOLETE  (VERIFIED solo si causa/resolución tienen evidencia)
lifecycle: open            # open | resolved | wont_fix  (ciclo de vida del incidente; no es un estado de conocimiento)
date: YYYY-MM-DD
resolved_on:               # YYYY-MM-DD cuando lifecycle = resolved
area: <backend | frontend | persistence | agents | providers | infra | process>
severity: <low | medium | high>
source: <observed-in-repo | test-output | command-output | user-provided | inferred>
related_commit: <hash donde se observó>
related_docs: []
related_solution: []       # enlaces a notas de 02_VERIFIED_SOLUTIONS
tags: []
---

# <Título>

## Síntoma
Qué se observó. Mensaje de error o salida **saneada** (sin claves, tokens, URLs con credenciales ni valores de `.env`).

## Contexto
Qué se estaba haciendo, rama/commit, entorno.

## Cómo reproducir
Pasos mínimos. Si no se pudo reproducir, indícalo.

## Causa
- **Confirmada** (con evidencia): ...
- **Sospechada** (hipótesis, no hecho): ...

## Evidencia de la causa
Comando/salida/test que demuestra la causa confirmada. Si solo hay sospecha, escribe «sin evidencia».

## Resolución
Qué se hizo. Si la solución está comprobada, enlaza la nota de `02_VERIFIED_SOLUTIONS/`; si no, indica «sin verificar».

## Prevención
Test, regla o documentación que evitaría repetirlo.

## Documentación oficial relacionada
Enlaces. Indica si el incidente revela una ambigüedad o contradicción en `docs/` (en ese caso, plantear revisión explícita).
