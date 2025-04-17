
import psycopg2
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import os
from jinja2 import Environment, FileSystemLoader

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT", 5432)
)
cursor = conn.cursor()

env = Environment(loader=FileSystemLoader('templates'))

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            template = env.get_template('index.html')
            content = template.render()
            self.respond(content, "text/html")
        elif self.path == '/administrar.html':
            cursor.execute("SELECT * FROM personas")
            personas = cursor.fetchall()
            template = env.get_template('administrar.html')
            content = template.render(personas=personas)
            self.respond(content, "text/html")
        elif self.path.startswith("/eliminar"):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            id_persona = params.get('id', [None])[0]
            if id_persona:
                cursor.execute("DELETE FROM personas WHERE id = %s", (id_persona,))
                conn.commit()
            self.send_response(302)
            self.send_header('Location', '/administrar.html')
            self.end_headers()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/guardar":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode())

            dni = params.get('dni', [''])[0]
            nombre = params.get('nombre', [''])[0]
            apellido = params.get('apellido', [''])[0]
            direccion = params.get('direccion', [''])[0]
            telefono = params.get('telefono', [''])[0]

            cursor.execute("""
                INSERT INTO personas (dni, nombre, apellido, direccion, telefono)
                VALUES (%s, %s, %s, %s, %s)
            """, (dni, nombre, apellido, direccion, telefono))
            conn.commit()

            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

    def respond(self, content, content_type):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(content.encode())

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 10000))
    with HTTPServer(("", PORT), MyHandler) as server:
        print(f"Servidor corriendo en puerto {PORT}")
        server.serve_forever()
