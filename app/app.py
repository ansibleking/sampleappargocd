import os
import psycopg
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

DSN = (
    f"host={os.environ.get('DB_HOST', 'localhost')} "
    f"port={os.environ.get('DB_PORT', '5432')} "
    f"dbname={os.environ.get('DB_NAME', 'inventory')} "
    f"user={os.environ.get('DB_USER', 'inventory')} "
    f"password={os.environ.get('DB_PASSWORD', '')}"
)
VERSION = os.environ.get("APP_VERSION", "dev")

PAGE = """
<!doctype html>
<title>Inventory</title>
<style>
  body { font-family: sans-serif; max-width: 720px; margin: 40px auto; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border-bottom: 1px solid #ddd; padding: 6px; text-align: left; }
  .ver { color: #888; font-size: 12px; }
</style>
<h1>Inventory</h1>
<p class="ver">version {{ version }} &middot; {{ rows|length }} items &middot; total qty {{ total }}</p>
<form method="post" action="/add">
  <input name="name" placeholder="Item name" required>
  <input name="qty" type="number" min="0" value="1" required>
  <button>Add</button>
</form>
<table>
  <tr><th>ID</th><th>Name</th><th>Qty</th><th></th></tr>
  {% for id, name, qty in rows %}
  <tr><td>{{ id }}</td><td>{{ name }}</td><td>{{ qty }}</td>
      <td><form method="post" action="/delete/{{ id }}"><button>Delete</button></form></td></tr>
  {% endfor %}
</table>
"""


def run(sql, params=None, fetch=True):
    with psycopg.connect(DSN, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall() if fetch else None


@app.get("/")
def index():
    rows = run("SELECT id, name, qty FROM items ORDER BY id")
    total = sum(r[2] or 0 for r in rows)
    return render_template_string(PAGE, rows=rows, total=total, version=VERSION)


@app.post("/add")
def add():
    name = request.form.get("name", "").strip()
    qty = int(request.form.get("qty", 0))
    if name:
        run("INSERT INTO items(name, qty) VALUES (%s, %s)", (name, qty), fetch=False)
    return redirect("/")


@app.post("/delete/<int:item_id>")
def delete(item_id):
    run("DELETE FROM items WHERE id = %s", (item_id,), fetch=False)
    return redirect("/")


@app.get("/healthz")
def healthz():
    run("SELECT 1")
    return "ok"
