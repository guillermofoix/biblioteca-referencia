# Biblioteca del aula

[![CI](https://github.com/guillermofoix/biblioteca-referencia/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/guillermofoix/biblioteca-referencia/actions/workflows/ci.yml)

Aplicación web sencilla para gestionar los libros de un aula: listar, buscar por título o autor, añadir, editar y borrar libros. Está hecha con Flask y guarda los datos en PostgreSQL.

## Requisitos

- Python 3.12
- PostgreSQL 14 o superior, con una base de datos vacía creada de antemano (por ejemplo, `biblioteca`) y un usuario con permisos sobre ella.

## Dependencias

Están fijadas en `requirements.txt`:

- Flask 3.0.3
- psycopg 3.2.3 (`psycopg[binary]`), para hablar con PostgreSQL
- python-dotenv 1.0.1, para leer un fichero `.env` si existe (opcional)

## Variables de entorno

| Nombre         | Para qué sirve                                                                                                                                      | Ejemplo                                                     |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `DATABASE_URL` | Dirección de conexión a PostgreSQL. **Obligatoria**: sin ella la app no arranca.                                                                    | `postgresql://usuario:contraseña@localhost:5432/biblioteca` |
| `SECRET_KEY`   | Clave para firmar los mensajes que se muestran al usuario. Si no se define, se usa una clave de desarrollo; en producción hay que poner una propia. | `una-clave-larga-y-secreta`                                 |

En local se pueden definir en un fichero `.env` en la raíz del proyecto (copia `.env.example` y cambia los valores).

## Ejecutarla en local

1. Crea la base de datos en PostgreSQL y copia `.env.example` a `.env` con tus datos.
2. Crea y activa un entorno virtual:

   **Linux / macOS**

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

   **Windows (PowerShell)**

   ```powershell
   py -3.12 -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
4. Arranca la aplicación:
   ```
   python app.py
   ```
5. Abre <http://localhost:5000> en el navegador.

## Puerto

La aplicación escucha en el puerto **5000**.

## Base de datos

La tabla `libros` se crea sola la primera vez que la app se conecta a la base de datos; no hay que ejecutar ningún script SQL.

## Comprobar el estado

La ruta `GET /health` indica si la app está viva y puede hablar con la base de datos (ejecuta un `SELECT 1`). Responde en JSON:

| Código | Respuesta                                  | Significado                                                       |
| ------ | ------------------------------------------ | ----------------------------------------------------------------- |
| 200    | `{"status": "ok", "db": "ok"}`             | Todo bien.                                                        |
| 503    | `{"status": "error", "db": "unreachable"}` | No se llega a la base de datos (o falta `DATABASE_URL`). El motivo real queda en los logs. |

No la usa una persona, sino un programa: más adelante la usaremos en el healthcheck de Docker y en la monitorización, para saber de forma automática si la app funciona.

Reto de despliegue: ver [docs/RETO_DESPLIEGUE.md](docs/RETO_DESPLIEGUE.md)
