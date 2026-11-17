import os
from datetime import datetime
from functools import wraps
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='agricultor')
    plots = db.relationship('Plot', backref='owner', cascade='all, delete-orphan')

class Plot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    crop = db.Column(db.String(100), nullable=False)
    area = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    observations = db.relationship('Observation', backref='plot', cascade='all, delete-orphan')

class Observation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plot_id = db.Column(db.Integer, db.ForeignKey('plot.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    rainfall = db.Column(db.Float, nullable=False)
    soil_moisture = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(40), nullable=False, default='Manual')

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY', 'solo-desarrollo-cambiar-en-produccion'), SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(app.instance_path, 'agronasa.db')), SQLALCHEMY_TRACK_MODIFICATIONS=False)
    if test_config: app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    with app.app_context(): db.create_all()

    def login_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if 'uid' not in session:
                flash('Inicia sesión para continuar.', 'warning')
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapper

    def current_user():
        return db.session.get(User, session.get('uid')) if session.get('uid') else None

    def get_plot(plot_id):
        plot = db.get_or_404(Plot, plot_id)
        u = current_user()
        if not u or (u.role != 'admin' and plot.user_id != u.id): abort(403)
        return plot

    @app.context_processor
    def inject_user(): return {'user': current_user()}

    @app.route('/')
    def index(): return render_template('index.html')

    @app.route('/registro', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            if not name or '@' not in email or len(password) < 8:
                flash('Completa los campos y usa una contraseña de al menos 8 caracteres.', 'danger')
            elif User.query.filter_by(email=email).first():
                flash('El correo ya está registrado.', 'danger')
            else:
                db.session.add(User(name=name, email=email, password_hash=generate_password_hash(password)))
                db.session.commit()
                flash('Cuenta creada. Inicia sesión.', 'success')
                return redirect(url_for('login'))
        return render_template('auth.html', mode='registro')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            u = User.query.filter_by(email=email).first()
            if u and check_password_hash(u.password_hash, request.form.get('password', '')):
                session.clear(); session['uid'] = u.id
                return redirect(url_for('dashboard'))
            flash('Credenciales incorrectas.', 'danger')
        return render_template('auth.html', mode='login')

    @app.post('/logout')
    @login_required
    def logout(): session.clear(); return redirect(url_for('index'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        u = current_user()
        plots = Plot.query if u.role == 'admin' else Plot.query.filter_by(user_id=u.id)
        records = plots.order_by(Plot.id.desc()).all()
        observations = sum(len(p.observations) for p in records)
        return render_template('dashboard.html', plots=records, observations=observations, area=sum(p.area for p in records))

    @app.route('/parcelas/nueva', methods=['GET', 'POST'])
    @login_required
    def plot_new():
        if request.method == 'POST':
            try:
                area = float(request.form['area'])
                if area <= 0: raise ValueError()
                lat = float(request.form['latitude']) if request.form.get('latitude') else None
                lon = float(request.form['longitude']) if request.form.get('longitude') else None
                if lat is not None and not -90 <= lat <= 90: raise ValueError()
                if lon is not None and not -180 <= lon <= 180: raise ValueError()
                if not all(request.form.get(k, '').strip() for k in ('name','location','crop')): raise ValueError()
                db.session.add(Plot(name=request.form['name'].strip(), location=request.form['location'].strip(), crop=request.form['crop'].strip(), area=area, latitude=lat, longitude=lon, user_id=session['uid']))
                db.session.commit(); flash('Parcela registrada.', 'success'); return redirect(url_for('dashboard'))
            except (ValueError, KeyError): flash('Verifica los datos de la parcela.', 'danger')
        return render_template('plot_form.html', plot=None)

    @app.route('/parcelas/<int:plot_id>/editar', methods=['GET','POST'])
    @login_required
    def plot_edit(plot_id):
        plot = get_plot(plot_id)
        if request.method == 'POST':
            try:
                area = float(request.form['area'])
                if area <= 0 or not all(request.form.get(k, '').strip() for k in ('name','location','crop')): raise ValueError()
                lat = float(request.form['latitude']) if request.form.get('latitude') else None
                lon = float(request.form['longitude']) if request.form.get('longitude') else None
                if lat is not None and not -90 <= lat <= 90: raise ValueError()
                if lon is not None and not -180 <= lon <= 180: raise ValueError()
                plot.name=request.form['name'].strip(); plot.location=request.form['location'].strip(); plot.crop=request.form['crop'].strip(); plot.area=area; plot.latitude=lat; plot.longitude=lon
                db.session.commit(); flash('Parcela actualizada.', 'success'); return redirect(url_for('plot_detail', plot_id=plot.id))
            except (ValueError, KeyError): flash('Datos inválidos.', 'danger')
        return render_template('plot_form.html', plot=plot)

    @app.post('/parcelas/<int:plot_id>/eliminar')
    @login_required
    def plot_delete(plot_id):
        plot = get_plot(plot_id); db.session.delete(plot); db.session.commit()
        flash('Parcela eliminada.', 'success'); return redirect(url_for('dashboard'))

    def recommendation(obs):
        if not obs: return 'Registra una observación para recibir una orientación.'
        if obs.source == 'Manual' and obs.soil_moisture < 25: return 'Humedad del suelo baja: evaluar riego y verificar con medición de campo.'
        if obs.rainfall > 60: return 'Precipitación elevada: revisar drenaje y riesgo de encharcamiento.'
        if obs.temperature > 35: return 'Temperatura alta: vigilar estrés térmico y disponibilidad de agua.'
        return 'Condiciones registradas sin alertas de umbral; continuar monitoreo.'

    @app.route('/parcelas/<int:plot_id>')
    @login_required
    def plot_detail(plot_id):
        plot=get_plot(plot_id)
        records=Observation.query.filter_by(plot_id=plot.id).order_by(Observation.date.desc(), Observation.id.desc()).all()
        return render_template('plot_detail.html', plot=plot, records=records, recommendation=recommendation(records[0] if records else None))

    @app.post('/parcelas/<int:plot_id>/observaciones')
    @login_required
    def observation_new(plot_id):
        plot=get_plot(plot_id)
        try:
            day=datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            temp=float(request.form['temperature']); rain=float(request.form['rainfall']); moisture=float(request.form['soil_moisture'])
            if not (0 <= rain <= 2000 and 0 <= moisture <= 100 and -90 <= temp <= 70): raise ValueError()
            db.session.add(Observation(plot_id=plot.id, date=day, temperature=temp, rainfall=rain, soil_moisture=moisture))
            db.session.commit(); flash('Observación guardada.', 'success')
        except (ValueError, KeyError): flash('Observación inválida.', 'danger')
        return redirect(url_for('plot_detail', plot_id=plot.id))

    @app.post('/observaciones/<int:obs_id>/eliminar')
    @login_required
    def observation_delete(obs_id):
        obs=db.get_or_404(Observation, obs_id); plot=get_plot(obs.plot_id)
        db.session.delete(obs); db.session.commit(); flash('Observación eliminada.', 'success')
        return redirect(url_for('plot_detail', plot_id=plot.id))

    @app.route('/observaciones/<int:obs_id>/editar', methods=['GET','POST'])
    @login_required
    def observation_edit(obs_id):
        obs=db.get_or_404(Observation, obs_id); plot=get_plot(obs.plot_id)
        if request.method == 'POST':
            try:
                day=datetime.strptime(request.form['date'], '%Y-%m-%d').date()
                temp=float(request.form['temperature']); rain=float(request.form['rainfall']); moisture=float(request.form['soil_moisture'])
                if not (0 <= rain <= 2000 and 0 <= moisture <= 100 and -90 <= temp <= 70): raise ValueError()
                obs.date=day; obs.temperature=temp; obs.rainfall=rain; obs.soil_moisture=moisture
                db.session.commit(); flash('Observación actualizada.', 'success'); return redirect(url_for('plot_detail', plot_id=plot.id))
            except (ValueError, KeyError): flash('Observación inválida.', 'danger')
        return render_template('observation_form.html', obs=obs, plot=plot)

    @app.post('/parcelas/<int:plot_id>/nasa')
    @login_required
    def nasa_import(plot_id):
        plot=get_plot(plot_id)
        if plot.latitude is None or plot.longitude is None:
            flash('Ingresa latitud y longitud para consultar NASA POWER.', 'warning')
            return redirect(url_for('plot_detail', plot_id=plot.id))
        try:
            from datetime import timedelta
            end=datetime.utcnow().date()-timedelta(days=3)
            start=end-timedelta(days=7)
            params={'parameters':'T2M,PRECTOTCORR','community':'AG','longitude':plot.longitude,'latitude':plot.latitude,'start':start.strftime('%Y%m%d'),'end':end.strftime('%Y%m%d'),'format':'JSON'}
            response=requests.get('https://power.larc.nasa.gov/api/temporal/daily/point',params=params,timeout=12)
            response.raise_for_status()
            data=response.json()['properties']['parameter']
            inserted=0
            for key, temp in data['T2M'].items():
                rain=data['PRECTOTCORR'].get(key)
                if temp is None or rain is None or temp <= -900 or rain <= -900: continue
                day=datetime.strptime(key,'%Y%m%d').date()
                existing=Observation.query.filter_by(plot_id=plot.id,date=day,source='NASA POWER').first()
                if not existing:
                    # NASA POWER no ofrece humedad del suelo en esta consulta; no se inventa el dato.
                    db.session.add(Observation(plot_id=plot.id,date=day,temperature=float(temp),rainfall=max(0,float(rain)),soil_moisture=0,source='NASA POWER'))
                    inserted+=1
            db.session.commit(); flash(f'Se importaron {inserted} registros NASA POWER. Humedad de suelo = 0 significa dato no disponible para estas filas.', 'success')
        except (requests.RequestException, KeyError, ValueError, TypeError):
            flash('No se pudieron consultar datos NASA POWER. Inténtalo más tarde.', 'danger')
        return redirect(url_for('plot_detail', plot_id=plot.id))

    @app.route('/admin/usuarios')
    @login_required
    def admin_users():
        if current_user().role != 'admin': abort(403)
        return render_template('users.html', users=User.query.order_by(User.id).all())

    @app.post('/admin/usuarios/<int:user_id>/rol')
    @login_required
    def admin_role(user_id):
        if current_user().role != 'admin': abort(403)
        target=db.get_or_404(User,user_id)
        role=request.form.get('role')
        if role not in ('admin','agricultor') or target.id == session['uid']: abort(400)
        target.role=role; db.session.commit(); flash('Rol actualizado.', 'success')
        return redirect(url_for('admin_users'))

    @app.errorhandler(403)
    def forbidden(error): return render_template('error.html', code=403, message='No tienes permiso para acceder.'), 403
    @app.errorhandler(404)
    def missing(error): return render_template('error.html', code=404, message='Página no encontrada.'), 404
    return app

app=create_app()
if __name__=='__main__': app.run(debug=True)
