"""
Last Breath - Server Entry Point
Punto de inicio del servidor
"""
from src.app import create_app

app = create_app()

if __name__ == '__main__':
    print("🔧 Last Breath - Servidor iniciado")
    print("🌐 http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
