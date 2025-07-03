from app import app  # Importa la variable 'app' desde el paquete 'app' (es decir, desde app/__init__.py)

if __name__ == '__main__':
    # Esta condición asegura que el servidor solo se ejecute
    # si este script es ejecutado directamente.
    app.run(debug=True)