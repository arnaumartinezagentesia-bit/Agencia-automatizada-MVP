# 90_TEMPLATES

Plantillas para crear notas nuevas. Copia la plantilla a la carpeta de destino, renómbrala `AAAA-MM-DD_slug.md` y rellena **todos** los campos.

| Plantilla | Destino |
|---|---|
| [[TEMPLATE_DECISION]] | `01_DECISIONS/` |
| [[TEMPLATE_VERIFIED_SOLUTION]] | `02_VERIFIED_SOLUTIONS/` |
| [[TEMPLATE_INCIDENT]] | `03_INCIDENTS/` |
| [[TEMPLATE_EXPERIMENT]] | `04_EXPERIMENTS/` |
| [[TEMPLATE_CHANGELOG_ENTRY]] | `06_CHANGELOG/` |

Metadatos comunes: `type`, `status` (solo `PROPOSED` · `ACCEPTED` · `VERIFIED` · `OBSOLETE`; ver [Tipos y estados](../README.md#tipos-y-estados)), `date`, `area`, `source`, `related_commit`, `related_docs`, `tags`.

Valores de `source`: `official-docs` · `observed-in-repo` · `test-output` · `command-output` · `external-docs` · `user-provided` · `inferred`. Si es `inferred`, la nota **no** puede ser `VERIFIED` por esa sola vía. Toda nota nueva empieza en `PROPOSED`.

Reglas fijas: sin secretos, sin copiar `docs/`, sin presentar hipótesis como hechos.
