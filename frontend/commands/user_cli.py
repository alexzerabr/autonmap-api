import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
import secrets

from models import db, User
from utils import is_strong_password

@click.group()
def user():
    """Comandos para gerenciamento de usuários administradores."""
    pass

@user.command('create-admin')
@click.option('--first-name', prompt=True, help='Primeiro nome do admin.')
@click.option('--last-name', prompt=True, help='Sobrenome do admin.')
@click.option('--email', prompt=True, help='E-mail de contato do admin.')
@click.option('--username', prompt=True, help='Nome de usuário para login.')
@click.option('--password', prompt='Senha', hide_input=True, confirmation_prompt=True, help='Senha de acesso.')
@with_appcontext
def create_admin(first_name, last_name, email, username, password):
    """Cria um novo usuário com privilégios de administrador."""
    if not is_strong_password(password):
        click.echo(click.style("Erro: A senha é fraca. Deve ter no mínimo 8 caracteres e um símbolo.", fg='red'))
        return

    if User.query.filter_by(username=username).first():
        click.echo(click.style(f"Erro: Nome de usuário '{username}' já existe.", fg='red'))
        return
    
    if User.query.filter_by(email=email).first():
        click.echo(click.style(f"Erro: E-mail '{email}' já está em uso.", fg='red'))
        return

    new_admin = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        username=username,
        is_admin=True
    )
    new_admin.set_password(password)
    db.session.add(new_admin)
    db.session.commit()
    
    click.echo(click.style(f"Usuário administrador '{username}' criado com sucesso!", fg='green'))

@user.command('promote')
@click.argument('username')
@with_appcontext
def promote(username):
    """Promove um usuário existente a administrador."""
    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(click.style(f"Erro: Usuário '{username}' não encontrado.", fg='red'))
        return
    
    if user.is_admin:
        click.echo(click.style(f"Aviso: Usuário '{username}' já é um administrador.", fg='yellow'))
        return

    user.is_admin = True
    db.session.commit()
    click.echo(click.style(f"Usuário '{username}' promovido a administrador com sucesso!", fg='green'))

@user.command('demote')
@click.argument('username')
@with_appcontext
def demote(username):
    """Remove os privilégios de administrador de um usuário."""
    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(click.style(f"Erro: Usuário '{username}' não encontrado.", fg='red'))
        return
    
    if not user.is_admin:
        click.echo(click.style(f"Aviso: Usuário '{username}' não é um administrador.", fg='yellow'))
        return

    user.is_admin = False
    db.session.commit()
    click.echo(click.style(f"Privilégios de administrador removidos de '{username}'.", fg='green'))

@user.command('list-admins')
@with_appcontext
def list_admins():
    """Lista todos os usuários com privilégios de administrador."""
    admins = User.query.filter_by(is_admin=True).all()
    if not admins:
        click.echo("Nenhum usuário administrador encontrado.")
        return
    
    click.echo("Usuários Administradores:")
    for admin in admins:
        click.echo(f"- ID: {admin.id}, Username: {admin.username}, Email: {admin.email}")

def init_app(app):
    """Registra o grupo de comandos no app Flask."""
    app.cli.add_command(user)
