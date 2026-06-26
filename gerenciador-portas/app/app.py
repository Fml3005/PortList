import os
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "infra_ports")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mapeamentos (
            id SERIAL PRIMARY KEY,
            ambiente VARCHAR(20) NOT NULL,
            namespace VARCHAR(100) NOT NULL,
            deploy VARCHAR(100) NOT NULL,
            port INTEGER NOT NULL,
            nodeport INTEGER NOT NULL,
            link TEXT,
            CONSTRAINT uq_ambiente_nodeport UNIQUE (ambiente, nodeport)
        );
    """
    )
    conn.commit()
    cur.close()
    conn.close()


@app.route("/")
def index():
    aba_ativa = request.args.get("aba", "desenvolvimento")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        "SELECT * FROM mapeamentos WHERE ambiente = %s ORDER BY nodeport ASC",
        (aba_ativa,),
    )
    itens = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", itens=itens, aba_ativa=aba_ativa)


@app.route("/adicionar", methods=["POST"])
def adicionar():
    ambiente = request.form["ambiente"]
    namespace = request.form["namespace"]
    deploy = request.form["deploy"]
    port = request.form["port"]
    nodeport = request.form["nodeport"]
    link = request.form.get("link", "")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO mapeamentos (ambiente, namespace, deploy, port, nodeport, link) VALUES (%s, %s, %s, %s, %s, %s)",
            (ambiente, namespace, deploy, port, nodeport, link),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao inserir (NodePort duplicado no mesmo ambiente): {e}")

    return redirect(url_for("index", aba=ambiente))


@app.route("/editar", methods=["POST"])
def editar():
    id_item = request.form["id"]
    ambiente = request.form["ambiente"]
    namespace = request.form["namespace"]
    deploy = request.form["deploy"]
    port = request.form["port"]
    nodeport = request.form["nodeport"]
    link = request.form.get("link", "")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE mapeamentos SET namespace=%s, deploy=%s, port=%s, nodeport=%s, link=%s WHERE id=%s",
            (namespace, deploy, port, nodeport, link, id_item),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao editar: {e}")

    return redirect(url_for("index", aba=ambiente))


@app.route("/deletar/<int:id>")
def deletar(id):
    ambiente = request.args.get("aba", "desenvolvimento")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM mapeamentos WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index", aba=ambiente))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)