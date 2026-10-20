# 03_INCIDENTS

Errores e incidentes: qué falló, cómo se manifestó, qué causa se ha **demostrado** y cómo se resolvió.

- Plantilla: [[TEMPLATE_INCIDENT]]
- Distingue siempre causa **confirmada** de causa **sospechada** (hipótesis).
- Cuando se encuentre una solución comprobada, crea una nota en `02_VERIFIED_SOLUTIONS/` y enlázala desde el incidente.
- Estado de conocimiento (`status`): `PROPOSED` → `ACCEPTED` / `VERIFIED` (causa o resolución, solo con evidencia) → `OBSOLETE`.
- Ciclo de vida del incidente (campo aparte, `lifecycle`): `open` → `resolved` / `wont_fix`.
- Sanea los logs antes de pegarlos: sin claves, tokens, URLs con credenciales ni datos de `.env`.
