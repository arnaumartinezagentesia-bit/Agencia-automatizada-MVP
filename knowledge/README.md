# Knowledge — memoria documental del proyecto

Memoria versionada de **Agencia Automatizada MVP**: decisiones, soluciones verificadas, incidentes y experimentos que surgen durante el desarrollo. Son archivos Markdown planos; Obsidian es solo una interfaz para leerlos y editarlos.

> **Alcance.** Esta memoria es una herramienta de **desarrollo**. No forma parte del producto MVP-0, no la lee ni la escribe ningún agente de la agencia en ejecución y no tiene integración con el backend. Esa integración, si llega, requiere una especificación y una aprobación propias (en `docs/MVP_SCOPE.md` la memoria curada / Obsidian figura como MVP-5).

## Principio rector

**Esta memoria complementa a la documentación oficial; no la sustituye ni la contradice.**
La fuente de verdad sigue siendo `docs/`, en este orden de autoridad:

1. `docs/MVP_SCOPE.md`
2. `docs/ARCHITECTURE.md`
3. `docs/DATA_CONTRACTS.md`
4. `docs/AGENT_SPEC.md`
5. `docs/UI_SPEC.md`
6. `docs/MASTER_DEVELOPMENT_PROMPT.md`

Si una nota choca con estos documentos, prevalece el documento oficial. La nota se corrige o se marca `OBSOLETE`; la contradicción solo se resuelve cambiando la especificación mediante una revisión explícita, nunca en silencio desde una nota.

## Áreas

| Carpeta | Contenido | Plantilla |
|---|---|---|
| [`00_START_HERE/`](00_START_HERE/) | Índice y guía de uso. Punto de entrada. | — |
| [`01_DECISIONS/`](01_DECISIONS/) | Decisiones técnicas que no están (o no con este detalle) en `docs/`. | `TEMPLATE_DECISION` |
| [`02_VERIFIED_SOLUTIONS/`](02_VERIFIED_SOLUTIONS/) | Soluciones comprobadas con evidencia concreta. | `TEMPLATE_VERIFIED_SOLUTION` |
| [`03_INCIDENTS/`](03_INCIDENTS/) | Errores e incidentes: síntoma, causa, resolución. | `TEMPLATE_INCIDENT` |
| [`04_EXPERIMENTS/`](04_EXPERIMENTS/) | Hipótesis y experimentos, aún sin confirmar. | `TEMPLATE_EXPERIMENT` |
| [`05_AGENT_PLAYBOOKS/`](05_AGENT_PLAYBOOKS/) | Procedimientos de trabajo para Claude Code (no para los agentes de la agencia). | — |
| [`06_CHANGELOG/`](06_CHANGELOG/) | Registro de cambios relevantes en el propio conocimiento. | `TEMPLATE_CHANGELOG_ENTRY` |
| [`90_TEMPLATES/`](90_TEMPLATES/) | Plantillas de notas. | — |

## Tipos y estados

**Tipo** y **estado** son cosas distintas. El tipo dice *qué es* la nota; el estado dice *cuánto se puede confiar en ella*.

### Tipos (campo `type`)

| Tipo | Carpeta | Qué es |
|---|---|---|
| `decision` | `01_DECISIONS/` | Elección técnica con su contexto y alternativas. |
| `verified-solution` | `02_VERIFIED_SOLUTIONS/` | Solución a un problema concreto, con evidencia. |
| `incident` | `03_INCIDENTS/` | Error o fallo: síntoma, causa, resolución. |
| `experiment` | `04_EXPERIMENTS/` | Hipótesis o prueba aún por contrastar. |
| `changelog` | `06_CHANGELOG/` | Registro de un cambio en el propio conocimiento. |

El conocimiento **oficial** no es un tipo de nota: vive en `docs/` y aquí solo se enlaza.

### Estados (campo `status`)

Solo hay cuatro. Significan siempre lo mismo, sea cual sea el tipo:

| Estado | Significado | Lo que NO implica |
|---|---|---|
| `PROPOSED` | Contenido pendiente de revisión. | Que sea correcto ni aceptado. |
| `ACCEPTED` | Aceptado mediante **aprobación explícita** del responsable del proyecto. | Que esté demostrado experimentalmente. |
| `VERIFIED` | Afirmación técnica o solución respaldada por **evidencia concreta**, reproducible cuando corresponda y descrita en la propia nota. | Que alguien la haya aprobado: la aprobación no sustituye a la evidencia. |
| `OBSOLETE` | Conservado por historial; **ya no es referencia vigente**. Se enlaza al sustituto con `superseded_by` si lo hay. | Que se borre: nunca se elimina. |

Reglas:

- Toda nota nueva empieza en `PROPOSED`. Quien la redacta no puede ponerla en `ACCEPTED`: solo tras aprobación explícita, registrada en la nota (quién y cuándo).
- Una **decisión** no se considera aprobada hasta que está `ACCEPTED`. Una decisión no se «verifica»: se aprueba.
- Una **solución** técnica solo es `VERIFIED` con evidencia en la nota. La aprobación humana sola, sin pruebas, la deja como máximo en `ACCEPTED`.
- Una **hipótesis** (`type: experiment`) no puede ser `VERIFIED`. Si se confirma, se crea una nota nueva (solución o decisión) con su propia evidencia y se enlaza con `promoted_to`.
- Los **incidentes** y **experimentos** tienen además un campo de ciclo de vida propio (`lifecycle`, `stage`, `outcome`) que no es un estado de conocimiento.
- Si una nota choca con `docs/`, **prevalece la documentación oficial vigente** hasta que una modificación de `docs/` sea aprobada. La nota se corrige o pasa a `OBSOLETE`.
- Una nota `PROPOSED` u `OBSOLETE`, o una hipótesis, **no se puede citar como hecho**.

## Cómo localizar información

1. Empieza por [`00_START_HERE/INDEX.md`](00_START_HERE/INDEX.md).
2. Busca por palabra clave (búsqueda de Obsidian o `git grep -i "<término>" knowledge/`). Para la documentación oficial, busca en `docs/`.
3. Filtra por metadatos: `status`, `area`, `tags` (frontmatter YAML).
4. Lee siempre la sección «Documentación oficial relacionada» y comprueba que la nota sigue alineada con `docs/`.
5. No trates como hecho nada que esté `PROPOSED` u `OBSOLETE`, ni ninguna hipótesis (`type: experiment`).

## Cómo mantenerla

- **Una nota, un hecho o decisión.** Nombre de archivo: `AAAA-MM-DD_slug-corto.md`.
- **Copia una plantilla** de `90_TEMPLATES/` y rellena todos los metadatos. Toda nota nueva empieza en `PROPOSED`.
- **Añade la nota a [`INDEX.md`](00_START_HERE/INDEX.md)** en el mismo cambio.
- **Registra los cambios relevantes** en `06_CHANGELOG/` (alta, cambio de estado, obsolescencia).
- **No borres: marca `OBSOLETE`** y enlaza al sustituto con `superseded_by`.
- **Revisa en cada fase**: al cerrar una fase del plan, revisa las notas que la tocan; marca como `OBSOLETE` las que ya no apliquen.
- **Cambios por Git**: las notas se revisan como cualquier otro cambio (rama, diff, PR).
- **Enlaces**: enlaces relativos a `docs/` (p. ej. `../../docs/DATA_CONTRACTS.md`) y wikilinks entre notas.

## Qué NO va aquí

- Secretos de cualquier tipo: API keys, contraseñas, tokens, credenciales, valores de `.env`, cabeceras de autenticación. Tampoco volcados de logs que puedan contenerlos.
- Copias de `docs/` ni resúmenes que compitan con ellos.
- Afirmaciones sin evidencia presentadas como hechos.
- Razonamiento privado de modelos o trazas internas.

## Obsidian

La bóveda (*vault*) de Obsidian es la **raíz del repositorio**, no `knowledge/`. Así se puede navegar de las notas a `docs/` y a `CLAUDE.md` sin duplicar nada.

1. Obsidian → *Open folder as vault*.
2. Selecciona la raíz del repositorio (la carpeta que contiene `.git`, `docs/`, `backend/`, `frontend/` y `knowledge/`).
3. Abre el índice de entrada: `knowledge/00_START_HERE/INDEX.md`.
4. Déjalo en «Restricted mode»: no hacen falta plugins y no se debe instalar ninguno por defecto.

Obsidian creará `.obsidian/` en la raíz. Está en `.gitignore` y no se versiona.
