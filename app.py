"""Biblioteca del aula: aplicación web sencilla para gestionar libros."""
import os
import socket
import sys
from datetime import date

import psycopg
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg.rows import dict_row

# Si existe un fichero .env, carga sus variables (útil para trabajar en local)
load_dotenv()

# Dirección de la base de datos: postgresql://usuario:contraseña@host:5432/basedatos
DATABASE_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__)
# Clave para firmar los mensajes flash. En producción hay que cambiarla por una secreta.
app.secret_key = os.environ.get("SECRET_KEY", "clave-solo-para-desarrollo")


# Indica si ya hemos comprobado/creado la tabla desde que arrancó la app
tabla_creada = False


def conectar():
    """Abre una conexión nueva con la base de datos (las filas llegan como diccionarios)."""
    global tabla_creada
    if not DATABASE_URL:
        raise RuntimeError(
            "Falta la variable de entorno DATABASE_URL. "
            "Ejemplo: postgresql://usuario:contraseña@localhost:5432/biblioteca"
        )
    # Si la base de datos no responde (por ejemplo, un grupo de seguridad mal configurado),
    # nos rendimos a los 5 s: así el error queda en el log y se ve la página amable,
    # en lugar de que gunicorn corte la petición a los 30 s.
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5)
    # La tabla se crea la primera vez que nos conectamos (y no en el bloque main),
    # así funciona con `python app.py` y con cualquier servidor que importe el módulo.
    if not tabla_creada:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS libros (
                   id SERIAL PRIMARY KEY,
                   titulo TEXT NOT NULL,
                   autor TEXT NOT NULL,
                   anio INTEGER,
                   prestado BOOLEAN NOT NULL DEFAULT FALSE,
                   creado TIMESTAMP DEFAULT now()
               )"""
        )
        conn.commit()
        tabla_creada = True
    return conn


def validar(titulo, autor, anio_texto):
    """Comprueba los datos del formulario. Devuelve (lista_de_errores, anio)."""
    errores = []
    anio = None
    if not titulo:
        errores.append("El título es obligatorio.")
    if not autor:
        errores.append("El autor es obligatorio.")
    if anio_texto:  # El año es opcional, pero si se escribe debe ser válido
        try:
            anio = int(anio_texto)
            if not 1000 <= anio <= date.today().year:
                errores.append(f"El año debe estar entre 1000 y {date.today().year}.")
        except ValueError:
            errores.append("El año debe ser un número entero.")
    return errores, anio


@app.route("/")
def lista():
    q = request.args.get("q", "").strip()
    with conectar() as conn:
        # IMPORTANTE: los valores se pasan con %s y como parámetros aparte, nunca
        # pegados al texto de la consulta, para evitar la inyección SQL.
        libros = conn.execute(
            "SELECT * FROM libros WHERE titulo ILIKE %s OR autor ILIKE %s ORDER BY id",
            (f"%{q}%", f"%{q}%"),
        ).fetchall()
    return render_template("lista.html", libros=libros, q=q)


@app.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        autor = request.form.get("autor", "").strip()
        errores, anio = validar(titulo, autor, request.form.get("anio", "").strip())
        if not errores:
            with conectar() as conn:
                conn.execute(
                    "INSERT INTO libros (titulo, autor, anio) VALUES (%s, %s, %s)",
                    (titulo, autor, anio),
                )
            flash("Libro añadido correctamente.")
            return redirect(url_for("lista"))
        for error in errores:
            flash(error)
    return render_template("formulario.html", libro=request.form, editando=False)


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    with conectar() as conn:
        libro = conn.execute("SELECT * FROM libros WHERE id = %s", (id,)).fetchone()
        if libro is None:
            flash("Ese libro no existe.")
            return redirect(url_for("lista"))
        if request.method == "POST":
            titulo = request.form.get("titulo", "").strip()
            autor = request.form.get("autor", "").strip()
            errores, anio = validar(titulo, autor, request.form.get("anio", "").strip())
            prestado = request.form.get("prestado") == "on"
            if not errores:
                conn.execute(
                    "UPDATE libros SET titulo = %s, autor = %s, anio = %s, prestado = %s WHERE id = %s",
                    (titulo, autor, anio, prestado, id),
                )
                flash("Libro modificado correctamente.")
                return redirect(url_for("lista"))
            for error in errores:
                flash(error)
            libro = request.form  # Mantiene lo que escribió el usuario
    return render_template("formulario.html", libro=libro, editando=True, id=id)


@app.route("/borrar/<int:id>", methods=["POST"])
def borrar(id):
    with conectar() as conn:
        conn.execute("DELETE FROM libros WHERE id = %s", (id,))
    flash("Libro borrado.")
    return redirect(url_for("lista"))


@app.route("/health")
def health():
    """Comprueba que la app está viva y llega a la base de datos (para Docker y la monitorización)."""
    try:
        with conectar() as conn:
            conn.execute("SELECT 1")
    except (psycopg.Error, RuntimeError) as error:
        # Capturamos el error aquí y no en los errorhandlers de abajo, porque esos devuelven
        # error.html y quien consulta un healthcheck es un programa que espera JSON.
        # El detalle va solo al log: en la respuesta podría filtrar datos de conexión.
        app.logger.error("Healthcheck fallido: %s", error)
        return {"status": "error", "db": "unreachable"}, 503
    # Flask convierte el diccionario en una respuesta JSON automáticamente
    return {"status": "ok", "db": "ok"}, 200


@app.context_processor
def datos_comunes():
    """Variables disponibles en todas las plantillas (para el pie de página)."""
    return {"maquina": socket.gethostname()}


@app.errorhandler(psycopg.Error)
def error_base_datos(error):
    """Si falla la base de datos, muestra una página amable en vez de la traza."""
    # Así el error real aparece en los logs aunque el usuario vea una página amable
    app.logger.error("Error de base de datos: %s", error)
    return render_template("error.html"), 503


@app.errorhandler(RuntimeError)
def error_configuracion(error):
    """Si falta la configuración (por ejemplo DATABASE_URL), lo registra y muestra la misma página."""
    app.logger.error("Error de configuración: %s", error)
    return render_template("error.html"), 503


if __name__ == "__main__":
    if not DATABASE_URL:
        sys.exit(
            "Falta la variable de entorno DATABASE_URL.\n"
            "Ejemplo: postgresql://usuario:contraseña@localhost:5432/biblioteca\n"
            "Defínela en el sistema o en un fichero .env (mira .env.example)."
        )
    app.run(debug=True, port=5000)
