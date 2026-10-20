# CLAUDE.md

Instrucciones para Claude Code en este repositorio.

## Documentación oficial (fuente de verdad)

La documentación oficial está en `docs/`. Orden de autoridad (el superior prevalece):

1. `docs/MVP_SCOPE.md`
2. `docs/ARCHITECTURE.md`
3. `docs/DATA_CONTRACTS.md`
4. `docs/AGENT_SPEC.md`
5. `docs/UI_SPEC.md`
6. `docs/MASTER_DEVELOPMENT_PROMPT.md`

Ante ambigüedad o contradicción en estos documentos, detente e informa de la sección exacta; no inventes una solución. El repositorio legacy no es fuente de verdad.

## Memoria del proyecto (`knowledge/`)

`knowledge/` es una memoria documental en Markdown (Obsidian es solo la interfaz). **Complementa** a `docs/`; no la sustituye. Es una herramienta de desarrollo: no está conectada al código de ejecución de los agentes de la agencia y no debes conectarla sin una especificación y aprobación explícitas.

### Uso de la memoria

1. **Antes de una tarea**: lee `knowledge/00_START_HERE/INDEX.md`, busca notas relevantes y lee la documentación oficial aplicable de `docs/`.
2. **Ante un error**: busca primero en `knowledge/02_VERIFIED_SOLUTIONS/` y `knowledge/03_INCIDENTS/` si ya se ha resuelto algo parecido.
3. **Distingue siempre** entre el conocimiento oficial (`docs/`) y las notas, y dentro de las notas entre **tipo** (`type`: decision, verified-solution, incident, experiment, changelog) y **estado** (`status`). Cita ambos al apoyarte en una nota. Los estados son solo cuatro:
   - `PROPOSED`: pendiente de revisión.
   - `ACCEPTED`: aceptado mediante aprobación explícita del usuario; no implica que se haya demostrado experimentalmente.
   - `VERIFIED`: respaldado por evidencia concreta, reproducible cuando corresponda y descrita en la nota.
   - `OBSOLETE`: conservado por historial; ya no es referencia vigente.
   Nunca trates como hecho una nota `PROPOSED` u `OBSOLETE`, ni una hipótesis (`type: experiment`).
4. **Puedes proponer y redactar notas nuevas** tras investigar un error o completar una tarea, usando las plantillas de `knowledge/90_TEMPLATES/` y añadiéndolas a `INDEX.md`. Toda nota nueva nace `PROPOSED`. Nunca pongas `ACCEPTED` sin una aprobación explícita del usuario, y nunca la atribuyas al usuario si no la ha dado. Las notas se entregan para revisión como cualquier cambio; no hagas commit sin que se pida.
5. **`VERIFIED` solo con evidencia concreta** (comando ejecutado, resultado observado, test que pasa, commit) registrada en la sección «Evidencia de verificación». La aprobación humana no sustituye a la evidencia: sin pruebas, la nota queda `PROPOSED` o, a lo sumo, `ACCEPTED`. Las decisiones no se «verifican»: se aprueban.
6. **Nunca conviertas una hipótesis en un hecho.** Un experimento nunca es `VERIFIED`: si se confirma, se crea una nota nueva con su propia evidencia. Ninguna nota puede contradecir la documentación oficial vigente: en caso de conflicto prevalece `docs/` hasta que una modificación sea aprobada. Si crees que `docs/` debe cambiar, plantea una revisión explícita al usuario; no la resuelvas desde una nota.
7. **Escribir una nota no es aprender.** No afirmes que has aprendido algo de forma permanente por haberlo anotado: en las tareas posteriores debes consultar la memoria (regla 1).
8. **Sin secretos en las notas**: ni API keys, contraseñas, tokens, credenciales, valores de `.env`, cabeceras de autenticación ni logs sin sanear.
9. **No registres como verificada** una solución solo porque parezca razonable o porque se haya aplicado un cambio sin comprobar su resultado.
10. **No borres notas**: márcalas `OBSOLETE` y enlaza a lo vigente (`superseded_by`).

### Obsidian

La bóveda de Obsidian es la raíz del repositorio; el índice de entrada es `knowledge/00_START_HERE/INDEX.md`. No instales plugins ni cambies configuración de Obsidian. `.obsidian/` está ignorado por Git.
