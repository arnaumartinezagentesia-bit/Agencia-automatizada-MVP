# 02_VERIFIED_SOLUTIONS

Soluciones a problemas concretos que han sido **comprobadas con evidencia**.

- Plantilla: [[TEMPLATE_VERIFIED_SOLUTION]]
- `status: VERIFIED` solo si la sección «Evidencia de verificación» contiene pruebas concretas: comando ejecutado, resultado observado, test que pasa, commit. «Parece razonable» o «el cambio se aplicó» **no es evidencia**.
- Sin evidencia, la nota se queda en `PROPOSED` (o `ACCEPTED` si hay aprobación humana pero no pruebas), o es una hipótesis en `04_EXPERIMENTS/`. La aprobación humana no sustituye a la evidencia.
- Una solución verificada vale para la versión/commit y entorno indicados. Si cambian, revalídala o márcala `OBSOLETE`.
- Estados: `PROPOSED` → (`ACCEPTED`) → `VERIFIED` → `OBSOLETE`.
- Nunca incluyas secretos ni valores de `.env` en comandos o salidas pegadas.
