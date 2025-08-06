# Role-Based Document Accessibility System - All in One File
# Technologies: Flask, SQLite3, HTML, CSS (with Bootstrap)

from flask import Flask, request, redirect, render_template_string, session, send_file, url_for
import sqlite3, os
from werkzeug.utils import secure_filename
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'secret123'
UPLOAD_FOLDER = 'uploads'
DB_NAME = 'rbdas.db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database Setup
with sqlite3.connect(DB_NAME) as conn:
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        filename TEXT,
        content TEXT,
        owner_id INTEGER,
        FOREIGN KEY(owner_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id INTEGER,
        shared_with_id INTEGER,
        access_type TEXT,
        FOREIGN KEY(doc_id) REFERENCES documents(id),
        FOREIGN KEY(shared_with_id) REFERENCES users(id)
    )''')

# HTML Template with Bootstrap and Navbar
base_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>RBDAS</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script>
        function confirmAction(message) {
            return confirm(message);
        }
    </script>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-light bg-light">
    <a class="navbar-brand" href="/dashboard">RBDAS</a>
    {% if session.email %}
    <div class="collapse navbar-collapse">
        <ul class="navbar-nav mr-auto">
            <li class="nav-item"><a class="nav-link" href="/upload">Upload</a></li>
            <li class="nav-item"><a class="nav-link" href="/delete">Delete</a></li>
            <li class="nav-item"><a class="nav-link" href="/share">Share</a></li>
        </ul>
        <span class="navbar-text mr-3">{{ session.email }}</span>
        <form method="POST" action="/logout">
            <button class="btn btn-danger btn-sm">Logout</button>
        </form>
    </div>
    {% endif %}
</nav>
<div class="container mt-4">
    {{ content|safe }}
</div>
</body>
</html>
'''

# Helper to get user ID and role
def get_user():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id, role FROM users WHERE email=?", (session['email'],))
        return c.fetchone()

@app.route('/')
def index():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
                conn.commit()
                session['email'] = email
                return redirect('/role')
            except:
                return 'Email already exists.'
    return render_template_string(base_template, content='''
        <h2>Register</h2>
        <form method="POST">
            <input name="email" type="email" required class="form-control" placeholder="Email"><br>
            <input name="password" type="password" required class="form-control" placeholder="Password"><br>
            <button type="submit" class="btn btn-primary">Register</button>
        </form>
        <p class="mt-2">Already have an account? <a href="/login">Login here</a></p>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
            user = c.fetchone()
            if user:
                session['email'] = email
                return redirect('/role')
            return 'Invalid credentials.'
    return render_template_string(base_template, content='''
        <h2>Login</h2>
        <form method="POST">
            <input name="email" type="email" required class="form-control" placeholder="Email"><br>
            <input name="password" type="password" required class="form-control" placeholder="Password"><br>
            <button type="submit" class="btn btn-primary">Login</button>
        </form>
        <p class="mt-2">Don’t have an account? <a href="/register">Register here</a></p>
    ''')

@app.route('/role', methods=['GET', 'POST'])
def role():
    if 'email' not in session:
        return redirect('/login')
    if request.method == 'POST':
        role = request.form['role']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET role=? WHERE email=?", (role, session['email']))
            conn.commit()
        return redirect('/dashboard')
    return render_template_string(base_template, content='''
        <h2>Select Your Role</h2>
        <form method="POST">
            <select name="role" class="form-control" required>
                <option value="admin">Admin</option>
                <option value="editor">Editor</option>
                <option value="viewer">Viewer</option>
            </select><br>
            <button type="submit" class="btn btn-success">Continue</button>
        </form>
    ''')

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect('/login')
    user_id, role = get_user()
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id, title, filename FROM documents WHERE owner_id=?", (user_id,))
        owned_docs = c.fetchall()
        c.execute("""SELECT d.id, d.title, d.filename, u.email, p.access_type FROM documents d
                     JOIN permissions p ON d.id = p.doc_id
                     JOIN users u ON d.owner_id = u.id
                     WHERE p.shared_with_id=?""", (user_id,))
        shared_docs = c.fetchall()

    html = f"""
        <h2>{role.capitalize()} Dashboard</h2>
        <ul class="list-group mt-4">
            <li class="list-group-item active">Your Documents</li>
            {''.join([f'<li class="list-group-item">{doc[1]} ({Path(doc[2]).suffix[1:].upper()}) - <a href="/download/{doc[0]}">Download</a></li>' for doc in owned_docs])}
            {''.join([f'<li class="list-group-item">{doc[1]} ({Path(doc[2]).suffix[1:].upper()}) from {doc[3]} - <a href="/download/{doc[0]}">Download</a>' + (f' | <a href="/edit/{doc[0]}">Edit</a>' if doc[4] == 'edit' and role == 'editor' else '') + '</li>' for doc in shared_docs])}
        </ul>
    """
    return render_template_string(base_template, content=html)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'email' not in session:
        return redirect('/login')
    user_id, role = get_user()
    if role != 'admin': return 'Access denied.'
    if request.method == 'POST':
        file = request.files['file']
        title = request.form['title']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("INSERT INTO documents (title, filename, content, owner_id) VALUES (?, ?, ?, ?)", (title, filename, '', user_id))
                conn.commit()
            return redirect('/dashboard')
    return render_template_string(base_template, content='''
        <h2>Upload Document</h2>
        <form method="POST" enctype="multipart/form-data" onsubmit="return confirmAction('Upload this document?')">
            <input name="title" placeholder="Title" class="form-control" required><br>
            <input type="file" name="file" class="form-control-file" required><br><br>
            <button type="submit" class="btn btn-success">Upload</button>
        </form>
    ''')

@app.route('/edit/<int:doc_id>', methods=['GET', 'POST'])
def edit(doc_id):
    if 'email' not in session:
        return redirect('/login')
    user_id, role = get_user()
    if role != 'editor': return 'Access denied.'
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT filename FROM documents WHERE id=?", (doc_id,))
        row = c.fetchone()
        if not row: return 'Document not found.'
        filename = row[0]
        if not filename.endswith('.txt'):
            return 'Editing is only supported for .txt files.'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if request.method == 'POST':
            new_content = request.form['content']
            with open(filepath, 'w') as f:
                f.write(new_content)
            c.execute("UPDATE documents SET content=? WHERE id=?", (new_content, doc_id))
            conn.commit()
            return redirect('/dashboard')
        with open(filepath, 'r') as f:
            content = f.read()
    return render_template_string(base_template, content=f'''
        <h2>Edit Document</h2>
        <form method="POST" onsubmit="return confirmAction('Save changes?')">
            <textarea name="content" class="form-control" rows="10">{content}</textarea><br>
            <button type="submit" class="btn btn-warning">Save Changes</button>
        </form>
    ''')

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if 'email' not in session:
        return redirect('/login')
    user_id, role = get_user()
    if role != 'admin': return 'Access denied.'
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id, title FROM documents WHERE owner_id=?", (user_id,))
        docs = c.fetchall()
        if request.method == 'POST':
            doc_id = request.form['doc_id']
            c.execute("DELETE FROM documents WHERE id=?", (doc_id,))
            c.execute("DELETE FROM permissions WHERE doc_id=?", (doc_id,))
            conn.commit()
            return redirect('/dashboard')
    return render_template_string(base_template, content=f'''
        <h2>Delete Document</h2>
        <form method="POST" onsubmit="return confirmAction('Are you sure you want to delete?')">
            <select name="doc_id" class="form-control">
                {''.join([f'<option value="{doc[0]}">{doc[1]}</option>' for doc in docs])}
            </select><br>
            <button type="submit" class="btn btn-danger">Delete</button>
        </form>
    ''')

@app.route('/share', methods=['GET', 'POST'])
def share():
    if 'email' not in session:
        return redirect('/login')
    user_id, role = get_user()
    if role != 'admin': return 'Access denied.'
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id, title FROM documents WHERE owner_id=?", (user_id,))
        docs = c.fetchall()
        if request.method == 'POST':
            doc_id = request.form['doc_id']
            recipient = request.form['recipient']
            access = request.form['access']
            c.execute("SELECT id FROM users WHERE email=?", (recipient,))
            row = c.fetchone()
            if row:
                shared_with_id = row[0]
                c.execute("INSERT INTO permissions (doc_id, shared_with_id, access_type) VALUES (?, ?, ?)", (doc_id, shared_with_id, access))
                conn.commit()
                return redirect('/dashboard')
    return render_template_string(base_template, content=f'''
        <h2>Share Document</h2>
        <form method="POST" onsubmit="return confirmAction('Share this document?')">
            <select name="doc_id" class="form-control">
                {''.join([f'<option value="{doc[0]}">{doc[1]}</option>' for doc in docs])}
            </select><br>
            <input name="recipient" class="form-control" placeholder="Recipient Email" required><br>
            <select name="access" class="form-control">
                <option value="view">View</option>
                <option value="edit">Edit</option>
            </select><br>
            <button type="submit" class="btn btn-info">Share</button>
        </form>
    ''')

@app.route('/download/<int:doc_id>')
def download(doc_id):
    if 'email' not in session:
        return redirect('/login')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT filename FROM documents WHERE id=?", (doc_id,))
        row = c.fetchone()
        if row:
            filepath = os.path.join(UPLOAD_FOLDER, row[0])
            return send_file(filepath, as_attachment=True)
    return 'File not found.'

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('email', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
