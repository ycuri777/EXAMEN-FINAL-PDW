# AgroNASA | Propuesta de proyecto de **Monitoreo agrícola**

**Autor:** YIYE AARON CURI ALCANTARA · **Código:** 26104320

Aplicación Flask + SQLite para el desafío oficial NASA Space Apps Challenge 2026 [Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/).
Orientado al reto **Cambio de rumbo: Adaptando las granjas con datos de la NASA**


## Funcionalidades
- Registro, inicio y cierre de sesión; contraseñas con hash Werkzeug.
- Roles agricultor y administrador; autorización por propietario.
- CRUD de parcelas y observaciones ambientales.
- Panel de indicadores; orientaciones basadas en umbrales demostrativos.
- Consulta opcional a NASA POWER (temperatura T2M y precipitación PRECTOTCORR); requiere internet y coordenadas.
- 9 pruebas automatizadas con pytest.

## Instalación local
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Abrir http://127.0.0.1:5000. Para ejecutar pruebas: `python -m pytest -v`.

## Cuenta de administrador
No hay credenciales predefinidas inseguras. Registra un usuario y, desde una consola Python en la carpeta del proyecto, ejecuta:
```python
from app import app, db, User
with app.app_context():
    user = User.query.filter_by(email='TU_CORREO').first()
    user.role = 'admin'
    db.session.commit()
```

## Publicación en GitHub y Render
1. Crea un repositorio público en GitHub, sube estos archivos (no subas `instance/`, bases de datos ni `.env`).
2. En Render: New > Web Service > Connect GitHub > selecciona repositorio. Usa `pip install -r requirements.txt` como build command y `gunicorn app:app` como start command.
3. Configura `SECRET_KEY` como variable de entorno segura. **Atención:** SQLite en el sistema de archivos efímero de Render puede perder datos con reinicios/despliegues. Para conservar SQLite, contrata/configura un disco persistente y `DATABASE_URL=sqlite:////var/data/agronasa.db` con el disco montado en `/var/data`; verifica compatibilidad con el plan. Sin disco, el despliegue es solo demostrativo.
4. Comprueba registro, login, CRUD, permisos y consulta NASA desde la URL pública.

## Evidencias
Añade capturas reales en `evidencias/` y reemplaza los marcadores:

| Evidencia | Captura |
|---|---|
| Inicio | Pendiente: `evidencias/01-inicio.png` |
| Registro/login | Pendiente: `evidencias/02-login.png` |
| Dashboard | Pendiente: `evidencias/03-dashboard.png` |
| CRUD | Pendiente: `evidencias/04-crud.png` |
| Pruebas | Pendiente: `evidencias/05-pytest.png` |
| Render | Pendiente: `evidencias/06-render.png` |

**GitHub:** pendiente de publicar.
**Render:** pendiente de desplegar.
**Certificado NASA:** pendiente de adjuntar si se dispone de constancia auténtica.

## Alcances y limitaciones
La aplicación no predice rendimiento agrícola ni realiza optimización agronómica real de rotación de cultivos; es un prototipo académico de apoyo a la decisión alineado temáticamente con Field Shift. Los umbrales son ilustrativos, no recomendaciones científicas validadas. NASA POWER no suministra humedad del suelo mediante esta consulta: se guarda un marcador 0 para las filas NASA y se muestra N/D en la interfaz. Para un producto de producción, conviene modelar ese dato como nullable, añadir CSRF, migraciones, PostgreSQL y controles adicionales.
