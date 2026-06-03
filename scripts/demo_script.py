import sys
from pathlib import Path
# ensure project root is on sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from backend import create_app
from backend import routes as backend_routes
from backend.db import get_user_by_username, get_credentials_for_user

app = create_app()
client = app.test_client()

username = 'demo_user'
password = 'DemoPass123!'

print('Registering user...')
r = client.post('/register', data={'username': username, 'password': password, 'confirm': password}, follow_redirects=True)
print('Register status:', r.status_code)

print('Logging in...')
r = client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)
print('Login status:', r.status_code)

print('Adding credential...')
r = client.post('/add', data={'service': 'ExampleService', 'account': 'demo@example.com', 'password': 'P@ssw0rd123'}, follow_redirects=True)
print('Add credential status:', r.status_code)

# Fetch user and credentials from DB
import backend
try:
    db_path = backend_routes.db_path
except AttributeError:
    db_path = str(Path(backend.DATA_DIR) / 'vault.db')

user = get_user_by_username(db_path, username)
print('User from DB:', user['id'], user['username'])
creds = get_credentials_for_user(db_path, user['id'])
print('Credentials count:', len(creds))
if creds:
    cid = creds[0]['id']
    print('Credential id:', cid)

    print('\nGetting dashboard HTML (snippet)...')
    r = client.get('/dashboard')
    html_snippet = r.get_data(as_text=True)
    # show small part
    start = html_snippet.find('<table')
    print(html_snippet[start:start+800])

    print('\nGetting audit page for credential id', cid)
    r = client.get(f'/audit/{cid}')
    print('Audit status:', r.status_code)
    print(r.get_data(as_text=True)[:800])
else:
    print('No credentials found.')
