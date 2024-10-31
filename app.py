from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
import os
import secrets
from uuid import uuid4  # Para IDs de sessão únicos

app = Flask(__name__)
app.secret_key = 'guedes90'

# Configurações do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:OXRlbi29015@177.87.122.164:3306/sistemanger'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'cleber.guedes@edu.mt.gov.br'
app.config['MAIL_PASSWORD'] = 'gnbs njed mvkm jwla'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Inicializações
db = SQLAlchemy(app)
mail = Mail(app)

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = None

# Modelos
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'))
    ip_address = db.Column(db.String(45), nullable=True)
    last_activity = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    session_id = db.Column(db.String(36), nullable=True)  # Coluna para armazenar o ID de sessão

    profile = db.relationship('Profile', backref='users', lazy=True)

class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    level = db.Column(db.Integer, nullable=False)

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expiration_time = db.Column(db.DateTime, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/')
@login_required
def home():
    return render_template('home.html', user=current_user)

@app.before_request
def check_activity():
    if current_user.is_authenticated:
        last_activity = session.get('last_activity')
        current_time = datetime.utcnow()

        if last_activity and last_activity.tzinfo is not None:
            last_activity = last_activity.replace(tzinfo=None)

        if last_activity and current_time - last_activity > timedelta(minutes=30):
            logout_user()
            session.clear()
            flash('Sua sessão foi encerrada por inatividade.', 'info')
            return redirect(url_for('login'))

        session['last_activity'] = current_time

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            if user.session_id:
                return render_template('confirm_logout.html', user=user)
            
            new_session_id = str(uuid4())
            user.session_id = new_session_id
            db.session.commit()

            login_user(user)
            session['last_activity'] = datetime.utcnow()
            session['session_id'] = new_session_id

            return redirect(url_for('home'))
        else:
            flash('E-mail ou senha incorretos.', 'error')

    return render_template('login.html')

@app.route('/confirm_login', methods=['POST'])
def confirm_login():
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)

    if user:
        new_session_id = str(uuid4())
        user.session_id = new_session_id
        db.session.commit()

        login_user(user)
        session['last_activity'] = datetime.utcnow()
        session['session_id'] = new_session_id

        flash('Sessão anterior desconectada. Bem-vindo(a) novamente!', 'info')
        return redirect(url_for('home'))

    flash('Erro ao confirmar login.', 'error')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    current_user.session_id = None
    db.session.commit()
    logout_user()
    session.clear()
    flash('Você foi desconectado.', 'success')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(16)
            expiration_time = datetime.utcnow() + timedelta(hours=1)

            reset_token = PasswordResetToken(token=token, user_id=user.id, expiration_time=expiration_time)
            db.session.add(reset_token)
            db.session.commit()

            msg = Message('Recuperação de Senha', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Acesse o link para redefinir sua senha: https://nger.onrender.com/reset-password/{token}'
            mail.send(msg)
            flash('E-mail de recuperação enviado!', 'success')
            return redirect(url_for('login'))
        else:
            flash('E-mail não encontrado.', 'error')
        
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if reset_token is None or reset_token.expiration_time < datetime.utcnow():
        flash('Token de redefinição inválido ou expirado.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        user = User.query.get(reset_token.user_id)

        if user:
            # Correção: utilizando 'pbkdf2:sha256' para criar o hash da nova senha
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            db.session.commit()
            db.session.delete(reset_token)
            db.session.commit()

            flash('Senha redefinida com sucesso! Você pode fazer login agora.', 'success')
            return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        # Correção: utilizando pbkdf2:sha256 para gerar a hash da senha no cadastro
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        profile_id = request.form['profile_id']

        new_user = User(nome=nome, email=email, password=password, profile_id=profile_id)
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!')
        return redirect(url_for('home'))

    profiles = Profile.query.all()
    print(f'Perfis encontrados: {len(profiles)}')
    for profile in profiles:
        print(f'ID: {profile.id}, Nome: {profile.name}')

    return render_template('register.html', profiles=profiles)


@app.route('/add_profile', methods=['GET', 'POST'])
def add_profile():
    if request.method == 'POST':
        name = request.form['name']
        level = request.form['level']
        new_profile = Profile(name=name, level=level)
        db.session.add(new_profile)
        db.session.commit()
        flash('Perfil cadastrado com sucesso!')
        return redirect(url_for('home'))
    return render_template('add_profile.html')

# Rota para usuário
@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        db.session.commit()
        flash('Usuário atualizado com sucesso!')
        return redirect(url_for('edit_user', id=user.id))
    return render_template('edit_user.html', user=user)

# Rota para editar usuário com AJAX
@app.route('/editar_user/<int:id>', methods=['GET', 'POST'])
def editar_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.nome = request.form['nome']
        user.email = request.form['email']
        user.profile_id = request.form['profile_id']
        db.session.commit()
        return jsonify(status='success')  # Retorna um JSON de sucesso

    profiles = Profile.query.all()
    return render_template('partials/editar_user.html', user=user, profiles=profiles)

# Rota para buscar usuários
@app.route('/search_user', methods=['GET'])
def search_user():
    query = request.args.get('query', '').strip()
    
    # Se houver um termo de busca, faz o filtro
    if query:
        users = User.query.join(Profile).filter(
            (User.nome.ilike(f'%{query}%')) |
            (User.email.ilike(f'%{query}%')) |
            (Profile.name.ilike(f'%{query}%'))
        ).all()
    else:
        users = User.query.options(joinedload(User.profile)).all()  # Carrega todos os usuários se não houver busca

    return render_template('partials/user_table.html', users=users)

# Rota para excluir usuário
@app.route('/delete_user', methods=['POST'])
def delete_user():
    user_id = request.form['user_id']
    
    # Excluir tokens de redefinição de senha relacionados ao usuário
    PasswordResetToken.query.filter_by(user_id=user_id).delete()
    
    # Excluir o usuário
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    return {'status': 'success'}, 200


# Rota para consultar perfis
@app.route('/search_profile', methods=['GET'])
def search_profile():
    query = request.args.get('query', '').strip()

    # Se houver um termo de busca, faz o filtro
    if query:
        profiles = Profile.query.filter(Profile.name.ilike(f'%{query}%')).all()
    else:
        profiles = Profile.query.all()  # Carrega todos os perfis se não houver busca

    return render_template('partials/profile_table.html', profiles=profiles)

# Rota para editar perfil
@app.route('/edit_profile/<int:id>', methods=['GET', 'POST'])
def edit_profile(id):
    profile = Profile.query.get_or_404(id)
    if request.method == 'POST':
        profile.name = request.form['profile_name']
        db.session.commit()
        flash('Perfil atualizado com sucesso!')
        return jsonify(status='success')  # Retorna um JSON de sucesso

    return render_template('partials/edit_profile.html', profile=profile)

# Rota para excluir perfil
@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    profile_id = request.form['profile_id']
    profile = Profile.query.get_or_404(profile_id)
    db.session.delete(profile)
    db.session.commit()
    return {'status': 'success'}, 200

# Rota para consultar perfis
@app.route('/consultar_perfil', methods=['GET'])
def consultar_perfil():
    query = request.args.get('query', '').strip()

    # Se houver um termo de busca, faz o filtro
    if query:
        profiles = Profile.query.filter(Profile.name.ilike(f'%{query}%')).all()
    else:
        profiles = Profile.query.all()  # Carrega todos os perfis se não houver busca

    return render_template('partials/consultar_perfil.html', profiles=profiles)

# Rota para página principal
@app.route('/principal')
def principal():
    return render_template('principal.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)