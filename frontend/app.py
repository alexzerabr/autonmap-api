import os
import requests
import secrets
import pyotp
import qrcode
import io
import base64
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_migrate import Migrate

from models import db, User
from utils import is_strong_password
from commands import user_cli

# --- Inicialização e Configuração ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "uma-chave-secreta-padrao-para-desenvolvimento")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)
user_cli.init_app(app)

# --- NOVO FILTRO JINJA ---
# Ensina o Jinja a converter uma string JSON de volta para um objeto Python.
def fromjson_filter(value):
    return json.loads(value)

app.jinja_env.filters['fromjson'] = fromjson_filter
# --- FIM DA CORREÇÃO ---


# --- Configurações Lidas do .env ---
FASTAPI_URL = os.getenv("FASTAPI_URL")
API_ADMIN_TOKEN = os.getenv("API_ADMIN_TOKEN")

# --- Decorators de Autenticação e Autorização ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Por favor, faça login para acessar esta página.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash("Você não tem permissão para acessar esta página.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rota da Documentação ---
@app.route("/docs")
@login_required
def docs():
    return render_template("docs.html")

# --- Rotas de Autenticação e 2FA (sem alterações) ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['is_admin'] = user.is_admin
            if user.is_2fa_enabled:
                session['2fa_user_id'] = user.id
                return redirect(url_for('verify_2fa'))
            else:
                session['setup_2fa_user_id'] = user.id
                return redirect(url_for('setup_2fa'))
        else:
            flash("Usuário ou senha inválidos.", "error")
            return render_template("login.html")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Você foi desconectado com sucesso.", "success")
    return redirect(url_for('login'))

@app.route("/setup-2fa", methods=["GET", "POST"])
def setup_2fa():
    user_id = session.get('setup_2fa_user_id')
    if user_id is None: return redirect(url_for('login'))
    user = User.query.get(user_id)
    if not user: return redirect(url_for('login'))
    if request.method == "POST":
        token = request.form.get("token")
        totp = pyotp.TOTP(user.otp_secret)
        if totp.verify(token):
            user.is_2fa_enabled = True
            db.session.commit()
            session.pop('setup_2fa_user_id', None)
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash("2FA ativado com sucesso! Faça bom uso dos seus códigos de backup.", "success")
            return redirect(url_for('index'))
        else:
            flash("Código 2FA inválido. Tente novamente.", "error")
    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        backup_codes_plain = [secrets.token_hex(6).upper() for _ in range(10)]
        user.hashed_backup_codes = json.dumps([generate_password_hash(code) for code in backup_codes_plain])
        db.session.commit()
    else:
        backup_codes_plain = ["(Seus códigos já foram gerados e exibidos. Guarde-os em segurança.)"]
    totp_uri = pyotp.totp.TOTP(user.otp_secret).provisioning_uri(name=user.email, issuer_name="autonmap-API")
    img = qrcode.make(totp_uri)
    buf = io.BytesIO()
    img.save(buf)
    qr_code_data = base64.b64encode(buf.getvalue()).decode('ascii')
    return render_template("setup_2fa.html", qr_code=qr_code_data, backup_codes=backup_codes_plain)

@app.route("/verify-2fa", methods=["GET", "POST"])
def verify_2fa():
    user_id = session.get('2fa_user_id')
    if user_id is None: return redirect(url_for('login'))
    if request.method == "POST":
        token = request.form.get("token").strip()
        user = User.query.get(user_id)
        if not user: return redirect(url_for('login'))
        totp = pyotp.TOTP(user.otp_secret)
        is_valid = totp.verify(token)
        if not is_valid:
            backup_codes_hashed = json.loads(user.hashed_backup_codes or '[]')
            for i, hashed_code in enumerate(backup_codes_hashed):
                if check_password_hash(hashed_code, token):
                    is_valid = True
                    backup_codes_hashed.pop(i)
                    user.hashed_backup_codes = json.dumps(backup_codes_hashed)
                    db.session.commit()
                    flash(f"Código de backup utilizado. Restam {len(backup_codes_hashed)} códigos.", "warning")
                    break
        if is_valid:
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash("Verificação 2FA bem-sucedida.", "success")
            return redirect(url_for('index'))
        else:
            flash("Código 2FA ou de backup inválido.", "error")
    return render_template("verify_2fa.html")
    
# --- Rotas de Perfil do Usuário ---
@app.route("/profile")
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template("profile.html", user=user)

@app.route("/profile/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    user = User.query.get(session['user_id'])
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        if not all([current_password, new_password, confirm_password]):
            flash("Todos os campos de senha são obrigatórios.", "error")
            return redirect(url_for('change_password'))
        if not user.check_password(current_password):
            flash("Senha atual incorreta.", "error")
            return redirect(url_for('change_password'))
        if new_password != confirm_password:
            flash("A nova senha e a confirmação não coincidem.", "error")
            return redirect(url_for('change_password'))
        if not is_strong_password(new_password):
            flash("A nova senha é fraca. Ela deve ter no mínimo 8 caracteres e incluir pelo menos um símbolo.", "error")
            return redirect(url_for('change_password'))
        if user.is_2fa_enabled:
            code_2fa = request.form.get("2fa_code", "").strip()
            if not pyotp.TOTP(user.otp_secret).verify(code_2fa):
                flash("Código 2FA inválido.", "error")
                return redirect(url_for('change_password'))
        user.set_password(new_password)
        db.session.commit()
        flash("Senha alterada com sucesso! Por favor, faça login novamente.", "success")
        return redirect(url_for('logout'))
    return render_template("change_password.html", user=user)

# --- Rota Principal (Gerenciamento de Tokens) ---
@app.route("/")
@login_required
def index():
    all_tokens = get_tokens()
    user_tokens = []
    if session.get('is_admin'):
        user_tokens = all_tokens
    else:
        for token in all_tokens:
            if token.get('owner_username') == session.get('username'):
                user_tokens.append(token)
    return render_template("index.html", tokens=user_tokens)

@app.route("/tokens/create", methods=["POST"])
@login_required
def create_token():
    headers = {"X-API-Token": API_ADMIN_TOKEN}
    token_name = request.form.get("name")
    scopes = request.form.getlist("scopes")
    never_expires = request.form.get("never_expires")
    if not session.get('is_admin'):
        scopes = [s for s in scopes if not s.startswith('admin:')]
        if not scopes:
            scopes = ['scan:read', 'scan:write']
    if never_expires:
        expires_in_days = None
    else:
        expires_in_days = int(request.form.get("expires_in_days", 30))
    payload = {
        "name": token_name, 
        "scopes": scopes, 
        "expires_in_days": expires_in_days,
        "owner_username": session.get('username')
    }
    try:
        response = requests.post(f"{FASTAPI_URL}/v1/tokens/", headers=headers, json=payload, timeout=5)
        response.raise_for_status()
        new_token_data = response.json()
        flash(json.dumps(new_token_data), 'new_token_data')
    except requests.exceptions.RequestException as e:
        error_detail = "Erro desconhecido."
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", error_detail)
            except json.JSONDecodeError:
                error_detail = e.response.text
        flash(f"Erro ao criar token: {error_detail}", "error")
    return redirect(url_for('index'))

# --- Rotas de Gerenciamento de Usuários ---
@app.route("/users")
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.id).all()
    return render_template("users.html", users=users)

@app.route("/users/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    form_data = request.form.to_dict()
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        username = request.form.get("username", "").strip().lower()
        is_admin = request.form.get("is_admin") == 'on'
        if not all([first_name, last_name, email, password, confirm_password]):
            flash("Todos os campos são obrigatórios.", "error")
            return render_template("create_user.html", form=form_data)
        if password != confirm_password:
            flash("A senha e a confirmação não coincidem.", "error")
            return render_template("create_user.html", form=form_data)
        if not is_strong_password(password):
            flash("A senha é fraca. Ela deve ter no mínimo 8 caracteres e incluir pelo menos um símbolo.", "error")
            return render_template("create_user.html", form=form_data)
        if not username:
            base_username = f"{first_name.lower().replace(' ','')}.{last_name.lower().replace(' ','')}"
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
        try:
            new_user = User(
                first_name=first_name, last_name=last_name, email=email, username=username,
                is_admin=is_admin
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash(f"Usuário '{username}' criado com sucesso!", "success")
            return redirect(url_for('manage_users'))
        except IntegrityError:
            db.session.rollback()
            flash(f"Erro: Nome de usuário '{username}' ou e-mail '{email}' já existe.", "error")
            return render_template("create_user.html", form=form_data)
    return render_template("create_user.html", form={})

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        new_username = request.form.get('username').strip().lower()
        new_email = request.form.get('email').strip()
        new_first_name = request.form.get('first_name').strip()
        new_last_name = request.form.get('last_name').strip()
        if not all([new_username, new_email, new_first_name, new_last_name]):
            flash("Todos os campos são obrigatórios.", "error")
            return render_template('edit_user.html', user=user)
        if new_username != user.username and User.query.filter_by(username=new_username).first():
            flash(f"Nome de usuário '{new_username}' já está em uso.", "error")
            return render_template('edit_user.html', user=user)
        if new_email != user.email and User.query.filter_by(email=new_email).first():
            flash(f"E-mail '{new_email}' já está em uso.", "error")
            return render_template('edit_user.html', user=user)
        user.username = new_username
        user.email = new_email
        user.first_name = new_first_name
        user.last_name = new_last_name
        try:
            db.session.commit()
            flash(f"Dados do usuário '{user.username}' atualizados com sucesso!", "success")
            return redirect(url_for('manage_users'))
        except IntegrityError:
            db.session.rollback()
            flash("Ocorreu um erro ao salvar. Verifique se o usuário ou e-mail já existem.", "error")
    return render_template('edit_user.html', user=user)

@app.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = secrets.token_urlsafe(12)
    user.set_password(new_password)
    user.is_2fa_enabled = False
    user.otp_secret = None
    user.hashed_backup_codes = None
    db.session.commit()
    flash(f"A senha para o usuário '{user.username}' foi resetada para: {new_password}", "success")
    flash("O 2FA também foi desativado.", "warning")
    return redirect(url_for('manage_users'))

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == session.get('user_id'):
        flash("Você não pode deletar sua própria conta.", "error")
        return redirect(url_for('manage_users'))
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f"Usuário '{user_to_delete.username}' deletado com sucesso.", "success")
    return redirect(url_for('manage_users'))

@app.route('/users/<int:user_id>/reset-2fa', methods=['POST'])
@login_required
@admin_required
def reset_2fa(user_id):
    user = User.query.get_or_404(user_id)
    user.is_2fa_enabled = False
    user.otp_secret = None
    user.hashed_backup_codes = None
    db.session.commit()
    flash(f"O 2FA para o usuário '{user.username}' foi resetado.", "success")
    return redirect(url_for('manage_users'))
    
@app.route("/revoke/<int:token_id>", methods=['POST'])
@login_required
def revoke(token_id):
    can_revoke = False
    if session.get('is_admin'):
        can_revoke = True
    else:
        all_tokens = get_tokens()
        token_to_revoke = next((t for t in all_tokens if t.get('id') == token_id), None)
        if token_to_revoke and token_to_revoke.get('owner_username') == session.get('username'):
            can_revoke = True
    if not can_revoke:
        flash("Você não tem permissão para revogar este token.", "error")
        return redirect(url_for('index'))
    headers = {"X-API-Token": API_ADMIN_TOKEN}
    try:
        response = requests.delete(f"{FASTAPI_URL}/v1/tokens/{token_id}", headers=headers, timeout=5)
        response.raise_for_status()
        flash(f"Token ID {token_id} revogado com sucesso!", "success")
    except requests.exceptions.RequestException as e:
        flash(f"Erro ao revogar token: {e}", "error")
    return redirect(url_for("index"))

def get_tokens():
    if not API_ADMIN_TOKEN:
        flash("Token da API não configurado no servidor do frontend!", "error")
        return []
    headers = {"X-API-Token": API_ADMIN_TOKEN}
    try:
        response = requests.get(f"{FASTAPI_URL}/v1/tokens/", headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        flash(f"Não foi possível buscar a lista de tokens: {e}", "error")
        return []
