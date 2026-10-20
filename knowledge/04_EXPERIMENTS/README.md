# 04_EXPERIMENTS

Hipótesis y experimentos. **Nada de lo que hay aquí es un hecho establecido** hasta que se convierta, con evidencia, en una solución verificada o en una decisión aprobada.

- Plantilla: [[TEMPLATE_EXPERIMENT]]
- Una hipótesis se redacta como pregunta o afirmación a contrastar, con criterio de éxito/fallo definido antes de ejecutar.
- Si el experimento confirma la hipótesis, crea una nota nueva en `02_VERIFIED_SOLUTIONS/` (o `01_DECISIONS/`) y enlázala; no cambies el estado del experimento a «verificado».
- Estado de conocimiento (`status`): `PROPOSED` → `ACCEPTED` → `OBSOLETE`. Un experimento **nunca** es `VERIFIED`: si se confirma, se promueve a una nota nueva.
- Ciclo de vida (campos aparte): `stage` = `hypothesis` / `running` / `concluded`, y `outcome` = `confirmed` / `refuted` / `inconclusive`.
