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
- gunicorn 23.0.0, servidor de producción con el que arranca la app dentro de la imagen Docker

## Variables de entorno

| Nombre         | Para qué sirve                                                                                                                                      | Ejemplo                                                     |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `DATABASE_URL` | Dirección de conexión a PostgreSQL. **Obligatoria**: sin ella `python app.py` se niega a arrancar; con gunicorn la app arranca, pero responde 503.  | `postgresql://usuario:contraseña@localhost:5432/biblioteca` |
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

La ruta `GET /health` indica si la app está viva y puede hablar con la base de datos (ejecuta un `SELECT 1`). En local: <http://localhost:5000/health>. Responde en JSON:

| Código | Respuesta                                  | Significado                                                                                                                                                                |
| ------ | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 200    | `{"status": "ok", "db": "ok"}`             | Todo bien.                                                                                                                                                                 |
| 503    | `{"status": "error", "db": "unreachable"}` | La app no puede usar la base de datos: no llega, las credenciales son incorrectas o no tiene permisos (también si falta `DATABASE_URL`). El motivo real queda en los logs. |

No la usa una persona, sino un programa: más adelante la usaremos en el healthcheck de Docker y en la monitorización, para saber de forma automática si la app funciona.

## Seguridad automática

- **Trivy** (en el job `build` del CI): escanea la imagen Docker recién construida en busca de vulnerabilidades conocidas (CVE), tanto en la imagen base como en las librerías de Python. Si encuentra alguna de gravedad alta o crítica que ya tenga arreglo, el CI se pone en rojo.
- Trivy también busca **secretos** (claves, contraseñas) que se hayan colado dentro de la imagen, además de vulnerabilidades.
- **Dependabot** (`.github/dependabot.yml`): cada lunes comprueba si hay versiones nuevas de las dependencias de Python, de la imagen base y de las acciones de GitHub, y abre un PR para actualizarlas.

**Si Trivy pone el CI en rojo**, mira en el log del job qué paquete tiene el fallo y en qué versión está arreglado:

1. **Librería de Python**: sube su versión en `requirements.txt`.
2. **Paquete del sistema (Debian) que ya tiene arreglo**: no hace falta tocar el `Dockerfile`. La imagen base es `python:3.12-slim`, una etiqueta que Docker Hub reconstruye cuando salen parches de Debian. El CI construye siempre sin caché (cada ejecución usa una máquina nueva de GitHub y descarga la versión actual de la imagen base), así que basta con volver a ejecutar el workflow (**Re-run jobs** en la pestaña Actions) cuando la imagen oficial se haya actualizado. Si sigue en rojo, es que aún no se ha reconstruido: espera un día o dos y repite.
3. **Secreto dentro de la imagen**: quítalo del repositorio o añádelo al `.dockerignore` y, sobre todo, cámbialo (contraseña o clave nueva): si ha estado en una imagen, hay que darlo por filtrado.
4. Solo si no se puede arreglar, añade el CVE a `.trivyignore` con un comentario que justifique el motivo. Ignorar un CVE sin justificarlo no está permitido.

**Dependabot y la imagen base**: como el `Dockerfile` usa la etiqueta `python:3.12-slim`, Dependabot solo propondrá cambios de versión de Python (por ejemplo, de 3.12 a 3.13), no los parches del sistema (esos llegan solos al reconstruir, como se explica arriba). Esos PR hay que revisarlos con calma, porque cambian la versión del lenguaje: conviene cambiar también `python-version` en el CI y `target-version` en `pyproject.toml`, para que los tests se ejecuten con la misma versión que la imagen.

**Para revisar un PR de Dependabot**: comprueba que el CI está en verde, lee en la descripción del PR qué cambia en la nueva versión (sobre todo si es una versión mayor, que puede romper cosas) y comprueba en tu EC2 que la aplicación sigue funcionando antes de fusionarlo. Esto importa sobre todo en los cambios de versión mayor de Flask, psycopg o gunicorn.

## Publicar una versión

Cuando el código de `main` está listo para usarse, se publica una **versión**: una imagen Docker con un número fijo que queda guardada en el registro de contenedores de GitHub (GHCR). Lo hace el workflow `.github/workflows/release.yml`.

### Números de versión (semver)

Usamos **versionado semántico** (semver): `MAYOR.MENOR.PARCHE`, por ejemplo `1.4.2`. Cada número dice qué tipo de cambio trae la versión:

| Número     | Cuándo se sube                                                                       | Ejemplo en esta app                                                                   |
| ---------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| **PARCHE** | Se arregla un fallo sin cambiar cómo se usa la app.                                  | La búsqueda no encontraba autores con tilde y ahora sí: `1.4.2` → `1.4.3`.            |
| **MENOR**  | Se añade algo nuevo y todo lo anterior sigue funcionando igual.                      | Se añade un campo opcional "editorial" a los libros: `1.4.3` → `1.5.0`.               |
| **MAYOR**  | Hay un cambio que rompe lo anterior: quien la despliegue tiene que cambiar algo.     | Se cambia `DATABASE_URL` por variables separadas (`DB_HOST`, `DB_USER`...): `1.5.0` → `2.0.0`. |

Al subir un número, los de su derecha vuelven a 0. La etiqueta en Git lleva una `v` delante (`v1.4.3`); la imagen, no (`1.4.3`). Si la etiqueta no tiene el formato `vX.Y.Z`, el workflow falla con un mensaje de error y no publica nada.

### Crear una release en GitHub

1. Asegúrate de que el CI de `main` está en verde.
2. En el repositorio, ve a **Releases** (columna derecha) → **Draft a new release**.
3. En **Choose a tag**, escribe la etiqueta nueva (por ejemplo, `v1.0.0`) y pulsa **Create new tag: v1.0.0 on publish**. Comprueba que el destino (**Target**) es `main`.
4. Pulsa **Generate release notes**: GitHub escribe la lista de cambios a partir de los PR fusionados desde la versión anterior. Puedes retocarla.
5. Pulsa **Publish release**.

### Qué hace el workflow

Al publicar la release, en la pestaña **Actions** aparece una ejecución del workflow **Release**, que:

1. Comprueba que la etiqueta tiene el formato `vX.Y.Z` y calcula el nombre de la imagen: `ghcr.io/usuario/repositorio`, siempre en minúsculas (GHCR no admite mayúsculas).
2. Construye la imagen con dos etiquetas: la versión (`:1.0.0`) y `:latest`.
3. La escanea con Trivy, igual que el CI. **Si encuentra vulnerabilidades graves, se para y no publica nada.**
4. Inicia sesión en GHCR con el token temporal que GitHub crea para cada ejecución (no hay que configurar ningún secreto) y sube las dos etiquetas.
5. Escribe un resumen en la página de la ejecución con el nombre de la imagen y el comando `docker pull`.

> **Aviso: la primera publicación puede fallar con `denied`.** La primera vez, el `docker push` puede terminar con un error `denied` en el último paso aunque las capas se hayan subido. No pasa nada: el paquete ya queda creado y vinculado al repositorio. Entra en la ejecución fallida en **Actions** y pulsa **Re-run failed jobs**; la segunda vez funciona.

La imagen se ve en la pestaña **Packages** de tu perfil de GitHub y en la columna derecha del repositorio (sección **Packages**).

### Visibilidad del paquete: privado o público

La primera vez que se publica, el paquete se crea **privado**. Para cambiarlo: abre el paquete → **Package settings** → **Danger Zone** → **Change visibility**.

- **Privado**: solo quien tenga permiso puede descargarlo. Para hacer `docker pull` desde la EC2, antes hay que ejecutar `docker login ghcr.io` con tu usuario y un **token personal** (Settings → Developer settings → Personal access tokens) con el permiso `read:packages`. Ese token se queda guardado en la EC2, así que hay que tratarlo como una contraseña.
- **Público**: cualquiera puede descargarlo sin iniciar sesión, así que en la EC2 basta con `docker pull`. Es lo más cómodo para este proyecto, pero solo si la imagen no contiene nada secreto (Trivy también lo comprueba, y los secretos van en variables de entorno, nunca dentro de la imagen).

### ¿`:latest` o una versión concreta?

`:latest` es cómodo para probar (`docker pull ghcr.io/usuario/repositorio:latest` siempre trae la última), pero **en producción se despliega una versión concreta**, por ejemplo `:1.4.3`:

- Sabes exactamente qué código está funcionando en el servidor.
- `:latest` cambia cada vez que se publica, así que dos servidores (o el mismo servidor en dos días distintos) podrían estar ejecutando versiones diferentes sin que nadie se dé cuenta.
- Si la versión nueva falla, **volver atrás** es tan sencillo como arrancar otra vez la anterior (`:1.4.2`), que sigue guardada en GHCR. Con `:latest` no sabrías a qué versión volver.

## Desplegar en la EC2

La EC2 no construye la imagen: descarga de GHCR la que publicó el workflow de release, que ya ha pasado los tests y el escaneo de Trivy. Así, lo que se ejecuta en la EC2 es exactamente lo que se probó.

1. **Ten Docker instalado** en la EC2, con el plugin de Compose (`docker compose version` debe responder).
2. **Consigue el `docker-compose.yml`** clonando el repositorio (solo hace falta ese fichero y `.env.example`, pero clonar es lo más sencillo):
   ```bash
   git clone https://github.com/guillermofoix/biblioteca-referencia.git
   cd biblioteca-referencia
   ```
3. **Crea el `.env`** a partir del ejemplo y rellena `DATABASE_URL`, `SECRET_KEY`, `IMAGEN` y `VERSION`:
   ```bash
   cp .env.example .env
   nano .env
   ```
   La contraseña de RDS no debe contener `@ : / # ? %`, porque rompen la URL de `DATABASE_URL`, ni `$`, porque Docker Compose lo interpretaría como el comienzo de una variable. Si tiene alguno, cámbiala.

   Si el paquete de GHCR es privado, antes tienes que hacer `docker login ghcr.io` (ver [Visibilidad del paquete](#visibilidad-del-paquete-privado-o-público)).
4. **Descarga la imagen**:
   ```bash
   docker compose pull
   ```
5. **Arranca el contenedor** en segundo plano:
   ```bash
   docker compose up -d
   ```
6. **Comprueba que está sano**:
   ```bash
   docker compose ps
   ```
   Al principio la columna STATUS pone `(health: starting)`. Espera unos 30 segundos y repite hasta que ponga `(healthy)`. Si pone `(unhealthy)`, la app no puede usar la base de datos: mira `docker compose logs app`. Docker **no** reinicia el contenedor por estar unhealthy; solo lo marca.

### Cambiar de versión o volver atrás

Edita `VERSION` en el `.env` (por ejemplo, de `1.0.0` a `1.1.0`, o de vuelta a `1.0.0` si la nueva falla) y repite:

```bash
docker compose pull
docker compose up -d
docker compose ps
```

Compose ve que la imagen ha cambiado y sustituye el contenedor por uno nuevo con la otra versión. La base de datos no se toca: está en RDS.

### Probar cambios antes de publicar una release

Si quieres probar en la EC2 un cambio que aún no está en ninguna release, construye la imagen a mano con la etiqueta `dev` (usa el mismo valor de `IMAGEN` que tienes en `.env`):

```bash
docker build -t ghcr.io/guillermofoix/biblioteca-referencia:dev .
```

Pon `VERSION=dev` en el `.env` y arranca con `docker compose up -d` (**sin** `pull`: esa imagen solo existe en la EC2, no en GHCR). Cuando termines, vuelve a poner una versión publicada.

## Despliegue automático

Al publicar una release, el despliegue en la EC2 también es automático (con una aprobación por medio):

```
publicar (máquina de GitHub)  ->  aprobación en "produccion"  ->  desplegar (runner de la EC2)
```

El job `desplegar` de `release.yml` llama al workflow reutilizable `.github/workflows/deploy.yml`, el mismo que se usa para desplegar a mano o volver atrás.

### El runner de la EC2

Un **runner** es el programa que ejecuta los jobs de GitHub Actions. Normalmente GitHub presta una máquina (`ubuntu-latest`); aquí hemos instalado uno **self-hosted** en la EC2, con las etiquetas `self-hosted` y `produccion`. Los jobs con `runs-on: [self-hosted, produccion]` se ejecutan en la EC2, así que pueden usar su Docker directamente.

**No hace falta abrir ningún puerto en la EC2**: el runner es quien se conecta a GitHub (por HTTPS, hacia fuera) y le pregunta si hay trabajo pendiente. GitHub nunca se conecta a la EC2. El grupo de seguridad sigue igual que antes.

El despliegue vive en una carpeta fija, `/home/ubuntu/despliegue-biblioteca`, con su `docker-compose.yml` y un `.env` que escribe el propio workflow a partir de los secrets. El proyecto de Compose se llama siempre `biblioteca` (`-p biblioteca`).

> **Antes del primer despliegue automático**, para el contenedor que arrancaste a mano en [Desplegar en la EC2](#desplegar-en-la-ec2) (`docker compose down` en la carpeta del repositorio clonado). Si sigue en marcha, ocupa el puerto 5000 y el nuevo no podrá arrancar.

### El environment `produccion`

Un **environment** es un "entorno de destino" con sus propias reglas y secrets. Se configura en el repositorio:

1. **Settings** → **Environments** → **New environment**, con el nombre `produccion`.
2. En **Deployment protection rules**, marca **Required reviewers** y añade quién puede aprobar despliegues (por ejemplo, tú). Guarda.
3. En **Environment secrets**, añade `DATABASE_URL` (la conexión a RDS) y `SECRET_KEY`. Solo los jobs que declaran `environment: produccion` pueden leerlos. Recuerda que la contraseña de `DATABASE_URL` no puede llevar `@ : / # ? %` ni `$` (el workflow la escribe tal cual en el `.env`).

### Aprobar un despliegue

Cuando termina el job `publicar`, la ejecución se queda en **Waiting** con el aviso *Review required*. Entra en la ejecución (pestaña **Actions**), pulsa **Review deployments**, marca `produccion` y pulsa **Approve and deploy**. Si pulsas **Reject**, la imagen queda publicada en GHCR, pero no se despliega.

El job comprueba que el contenedor llega a `healthy` (gracias al healthcheck y a `--wait`). Al terminar, el resumen de la ejecución muestra la versión desplegada, la anterior y el estado del contenedor.

### Volver atrás a mano (rollback)

**Actions** → **Deploy** (columna izquierda) → **Run workflow** → escribe la versión anterior **sin la v** (por ejemplo, `1.0.0`) → **Run workflow**. También pide aprobación. Solo se puede volver a versiones que tienen release: el workflow descarga el `docker-compose.yml` de la etiqueta `vX.Y.Z`.

> **La primera versión desplegable es la 1.1.0.** Las versiones anteriores (como la `1.0.0`) no se pueden desplegar con el workflow, porque su `docker-compose.yml` todavía construía la imagen (`build: .`) en vez de usar la de GHCR.

### Rollback automático

Si la versión nueva no llega a `healthy` en 120 segundos (o falla la descarga de la imagen), el workflow:

1. Muestra en el log las últimas líneas de la app, para ver por qué ha fallado.
2. Vuelve a poner en el `.env` la versión que había antes y la arranca de nuevo. La imagen anterior sigue en la EC2, así que no hace falta descargar nada.
3. Termina **en rojo** con un error que dice a qué versión ha vuelto. Aunque la app funcione, la versión nueva no está desplegada y hay que enterarse.

Si era el primer despliegue (no había versión anterior), solo informa del fallo.

### Aviso de seguridad

Un runner self-hosted ejecuta en **tu** EC2 el código del workflow. En un repositorio público, cualquiera puede abrir un pull request con un workflow modificado, así que:

- Activa **Settings** → **Actions** → **General** → **Require approval for all external contributors**: los workflows de personas de fuera no se ejecutan sin que tú los apruebes.
- **Nunca** uses `runs-on: self-hosted` en un workflow que se dispare con `pull_request`: el código de un desconocido se ejecutaría en tu servidor, con acceso a Docker y a tus secrets. El CI (`ci.yml`) usa siempre máquinas de GitHub (`ubuntu-latest`).

Reto de despliegue: ver [docs/RETO_DESPLIEGUE.md](docs/RETO_DESPLIEGUE.md)
