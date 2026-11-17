import pytest
from app import create_app, db, User, Plot, Observation
from werkzeug.security import check_password_hash

@pytest.fixture
def client(tmp_path):
    app=create_app({'TESTING':True,'SECRET_KEY':'test-key','SQLALCHEMY_DATABASE_URI':'sqlite:///'+str(tmp_path/'test.db')})
    with app.test_client() as c:
        yield c

def signup(c,email='ana@example.com'):
    return c.post('/registro',data={'name':'Ana','email':email,'password':'claveSegura123'},follow_redirects=True)

def signin(c,email='ana@example.com'):
    return c.post('/login',data={'email':email,'password':'claveSegura123'},follow_redirects=True)

def create_plot(c):
    return c.post('/parcelas/nueva',data={'name':'Parcela Norte','location':'Lima','crop':'Maíz','area':'2.5','latitude':'-12.1','longitude':'-77.0'},follow_redirects=True)

def test_index(client):
    assert client.get('/').status_code==200
    assert b'AgroNASA' in client.get('/').data

def test_register_and_password_hash(client):
    signup(client)
    with client.application.app_context():
        u=User.query.filter_by(email='ana@example.com').first()
        assert u is not None
        assert u.password_hash!='claveSegura123'
        assert check_password_hash(u.password_hash,'claveSegura123')

def test_login_logout(client):
    signup(client); r=signin(client)
    assert b'Panel agr' in r.data
    client.post('/logout')
    assert client.get('/dashboard').status_code==302

def test_plot_crud(client):
    signup(client);signin(client);create_plot(client)
    assert b'Parcela Norte' in client.get('/dashboard').data
    r=client.post('/parcelas/1/editar',data={'name':'Parcela Sur','location':'Cusco','crop':'Papa','area':'3'},follow_redirects=True)
    assert b'Parcela Sur' in r.data
    client.post('/parcelas/1/eliminar')
    assert b'Parcela Sur' not in client.get('/dashboard').data

def test_observation_crud(client):
    signup(client);signin(client);create_plot(client)
    r=client.post('/parcelas/1/observaciones',data={'date':'2026-11-10','temperature':'24','rainfall':'12','soil_moisture':'45'},follow_redirects=True)
    assert b'2026-11-10' in r.data
    r=client.post('/observaciones/1/editar',data={'date':'2026-11-11','temperature':'26','rainfall':'14','soil_moisture':'40'},follow_redirects=True)
    assert b'2026-11-11' in r.data
    client.post('/observaciones/1/eliminar')
    assert b'2026-11-11' not in client.get('/parcelas/1').data

def test_permissions(client):
    signup(client);signin(client);create_plot(client)
    assert client.get('/admin/usuarios').status_code==403
    client.post('/logout');signup(client,'otra@example.com');signin(client,'otra@example.com')
    assert client.get('/parcelas/1').status_code==403

def test_validation(client):
    signup(client);signin(client)
    r=client.post('/parcelas/nueva',data={'name':'X','location':'Y','crop':'Z','area':'-3'},follow_redirects=True)
    assert b'Verifica los datos' in r.data

def test_404(client):
    assert client.get('/no-existe').status_code==404

def test_admin_roles(client):
    signup(client);signup(client,'otra@example.com')
    with client.application.app_context():
        u=User.query.filter_by(email='ana@example.com').first();u.role='admin';db.session.commit()
    signin(client)
    assert client.get('/admin/usuarios').status_code==200
    client.post('/admin/usuarios/2/rol',data={'role':'admin'})
    with client.application.app_context(): assert db.session.get(User,2).role=='admin'
