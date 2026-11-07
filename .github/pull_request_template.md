## Qué cambia

<!-- Una o dos frases: qué hace este PR. -->

## Por qué

<!-- El motivo del cambio: qué problema resuelve o qué se necesitaba. -->

## Cómo lo he probado

<!-- Comandos ejecutados (pytest, ruff...), pruebas a mano en el navegador, etc. -->

## Auditoría de IA
- **¿Has usado IA?** (sí / no; si sí, qué herramienta):
- **Qué partes generó:**
- **Qué propuso la IA que tuviste que descartar, corregir o adaptar (y por qué):**
  <!-- Ej.: usaba psycopg2 en vez de psycopg 3; quité una opción que no hacía falta. -->
- **Qué has revisado y comprobado tú** (comandos ejecutados, ficheros leídos):
- **Explica con tus palabras la parte más importante del cambio** (2-3 frases):
- **Qué parte NO entiendes del todo** (si no hay ninguna, escribe «Ninguna»):
  <!-- Reconocer una duda NO baja la nota; fingir que lo entiendes todo, sí, si luego no sabes explicarlo. -->

## Checklist

- [ ] He ejecutado `ruff check .` y `pytest` en local.
- [ ] Revisaré que el CI quede en verde antes de pedir el merge.
- [ ] No se sube el `.env` ni ningún secreto (contraseñas, claves, URLs con usuario y contraseña).
- [ ] Si cambia algo de la configuración (variables de entorno, puertos...), el README sigue siendo correcto.
