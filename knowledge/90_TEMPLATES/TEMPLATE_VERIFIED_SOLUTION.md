---
title: <Problema resuelto en una frase>
type: verified-solution
status: PROPOSED           # PROPOSED | ACCEPTED | VERIFIED | OBSOLETE  (VERIFIED solo con evidencia; la aprobación humana no basta)
date: YYYY-MM-DD
verified_on: YYYY-MM-DD    # solo cuando status = VERIFIED
area: <backend | frontend | persistence | agents | providers | infra | process>
source: <observed-in-repo | test-output | command-output | external-docs | user-provided | inferred>
related_commit: <hash en el que se verificó>
environment: <SO, versiones relevantes de Python/Node/PostgreSQL/librerías>
related_docs: [<p. ej. docs/DATA_CONTRACTS.md §X>]
related_incident: []
superseded_by: []         # al pasar a OBSOLETE
tags: []
---

# <Título>

> `VERIFIED` exige evidencia concreta en la sección correspondiente. Sin ella, la nota se queda en `PROPOSED` o, con aprobación humana pero sin pruebas, en `ACCEPTED`. «Parece razonable» o «el cambio se aplicó» no es evidencia.

## Problema
Síntoma o necesidad, con el mensaje de error saneado (sin secretos) si aplica.

## Solución
Pasos o cambio exacto. Si es código, referencia archivo y commit en lugar de pegar grandes bloques.

## Evidencia de verificación
Obligatoria para `VERIFIED`. Incluye lo que se ejecutó y lo que se observó:

- Comando(s): `...`
- Resultado observado: `...` (p. ej. «N tests passed», código de salida, salida relevante)
- Antes / después: <comportamiento antes y después de aplicar la solución>
- Commit/versión en el que se comprobó: `...`
- Cómo reproducir la comprobación: ...

## Alcance y límites
Entorno y versiones en los que se ha comprobado. Qué NO se ha comprobado.

## Documentación oficial relacionada
Enlaces. Confirma que la solución es coherente con ellos: <sí / no / n/a>.

## Aprobación (si procede)
Si está `ACCEPTED`: quién aprobó, cuándo y dónde consta. La aprobación no sustituye a la evidencia.

## Revalidación
Cuándo debe volver a comprobarse (cambio de versión, de fase, etc.).
