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


## Publicación en GitHub y Render
1. Crea un repositorio público en GitHub, sube estos archivos (no subas `instance/`, bases de datos ni `.env`).
2. En Render: New > Web Service > Connect GitHub > selecciona repositorio. Usa `pip install -r requirements.txt` como build command y `gunicorn app:app` como start command.
3. Configura `SECRET_KEY` como variable de entorno segura. **Atención:** SQLite en el sistema de archivos efímero de Render puede perder datos con reinicios/despliegues. Para conservar SQLite, contrata/configura un disco persistente y `DATABASE_URL=sqlite:////var/data/agronasa.db` con el disco montado en `/var/data`; verifica compatibilidad con el plan. Sin disco, el despliegue es solo demostrativo.
4. Comprueba registro, login, CRUD, permisos y consulta NASA desde la URL pública.

## Alcances y limitaciones
La aplicación no predice rendimiento agrícola ni realiza optimización agronómica real de rotación de cultivos; es un prototipo académico de apoyo a la decisión alineado temáticamente con Field Shift. Los umbrales son ilustrativos, no recomendaciones científicas validadas. NASA POWER no suministra humedad del suelo mediante esta consulta: se guarda un marcador 0 para las filas NASA y se muestra N/D en la interfaz. Para un producto de producción, conviene modelar ese dato como nullable, añadir CSRF, migraciones, PostgreSQL y controles adicionales.

atte.
Yiye Aaron CURI ALCANTARA - 26104320

---
## Vitar el sitio
Clic aqui:
<h2 align="center">🌐 ACCESO AL SISTEMA WEB</h2>

<p align="center">
  <a href="https://examen-final-pdw.onrender.com/dashboard/">
    <img src="https://img.shields.io/badge/INGRESAR_AL_SISTEMA-CLICK_AQUÍ-red?style=for-the-badge">
  </a>
</p>
