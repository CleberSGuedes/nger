from flask import Flask, render_template, redirect, url_for, request, flash, session as flask_session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import pytz  # Import necessário para manipular fusos horários
from sqlalchemy.orm import joinedload
from sqlalchemy import func
import os
import secrets
from uuid import uuid4
from fip613 import run_fip613
from werkzeug.utils import secure_filename
import pandas as pd

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

# Configuração do diretório de uploads
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024  # Limite de 1 GB

# Garante que o diretório de upload existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Defina o fuso horário local para Cuiabá
local_timezone = pytz.timezone("America/Cuiaba")

# Inicializações
db = SQLAlchemy(app)
migrate = Migrate(app, db)
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
    session_id = db.Column(db.String(36), nullable=True)

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

class Fip613(db.Model):
    __tablename__ = 'fip613'
    id = db.Column(db.Integer, primary_key=True)
    data_atualizacao = db.Column(db.DateTime, nullable=False)
    ano = db.Column(db.Integer, nullable=True)
    data_arquivo = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Registro do usuário que fez a última atualização
    user = db.relationship("User", backref="fip613_updates")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
@login_required
def home():
    return render_template('home.html', user=current_user)

@app.before_request
def check_activity():
    # Inclui 'forgot_password' na lista de exceções para não bloquear a navegação para essa rota
    if request.endpoint in ('static', 'login', 'confirm_login', 'forgot_password'):
        return None

    if current_user.is_authenticated:
        user_from_db = db.session.get(User, current_user.id)
        if user_from_db and user_from_db.session_id != flask_session.get('session_id'):
            logout_user()
            flask_session.clear()
            flash('Sua sessão foi encerrada porque você fez login em outro dispositivo.', 'info')
            return redirect(url_for('login'))

        last_activity = flask_session.get('last_activity')
        current_time = datetime.utcnow()

        if last_activity:
            last_activity = last_activity.replace(tzinfo=None) if last_activity.tzinfo else last_activity
            if current_time - last_activity > timedelta(minutes=30):
                user_from_db.is_active = False
                user_from_db.session_id = None
                db.session.commit()
                logout_user()
                flask_session.clear()
                flash('Sua sessão foi encerrada por inatividade.', 'info')
                return redirect(url_for('login'))

        flask_session['last_activity'] = current_time

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
            user.is_active = True
            user.ip_address = request.remote_addr
            user.last_activity = datetime.utcnow()
            db.session.commit()

            login_user(user)
            flask_session['last_activity'] = datetime.utcnow()
            flask_session['session_id'] = new_session_id

            return redirect(url_for('home'))
        else:
            flash('E-mail ou senha incorretos.', 'error')

    return render_template('login.html')

@app.route('/confirm_login', methods=['POST'])
def confirm_login():
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    if user:
        user.session_id = None
        user.is_active = False
        db.session.commit()

        flash('Sessão anterior desconectada. Por favor, faça login novamente para acessar o sistema.', 'info')
        return redirect(url_for('login'))

    flash('Erro ao confirmar logout. Tente novamente.', 'error')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    user_from_db = User.query.get(current_user.id)
    if user_from_db:
        user_from_db.is_active = False
        user_from_db.session_id = None
        db.session.commit()
        
    logout_user()
    flask_session.clear()
    flash('Você foi desconectado.', 'success')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        logout_user()  # Garante que o usuário está desconectado antes de redefinir a senha.

    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(16)
            expiration_time = datetime.utcnow() + timedelta(hours=1)

            reset_token = PasswordResetToken(token=token, user_id=user.id, expiration_time=expiration_time)
            db.session.add(reset_token)
            db.session.commit()

            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Recuperação de Senha', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Acesse o link para redefinir sua senha: {reset_url}'
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
        flash('Token de redefinicao inválido ou expirado.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        user = User.query.get(reset_token.user_id)

        if user:
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
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        profile_id = request.form['profile_id']

        # Verifica se o email já existe no banco
        if User.query.filter_by(email=email).first():
            return jsonify(success=False, mensagem="O email já está em uso. Escolha outro.")

        try:
            new_user = User(nome=nome, email=email, password=password, profile_id=profile_id)
            db.session.add(new_user)
            db.session.commit()
            return jsonify(success=True, mensagem="Usuário cadastrado com sucesso!")
        except Exception as e:
            print(f"Erro ao cadastrar usuário: {e}")
            return jsonify(success=False, mensagem="Erro ao cadastrar usuário.")

    profiles = Profile.query.all()
    return render_template('register.html', profiles=profiles)

@app.route('/add_profile', methods=['GET', 'POST'])
def add_profile():
    if request.method == 'POST':
        name = request.form['name']
        level = request.form['level']

        # Verifica se o nome do perfil já existe
        if Profile.query.filter_by(name=name).first():
            return jsonify(success=False, mensagem="Erro: Este perfil já existe.")

        try:
            new_profile = Profile(name=name, level=level)
            db.session.add(new_profile)
            db.session.commit()
            return jsonify(success=True, mensagem="Perfil cadastrado com sucesso!")
        except Exception as e:
            print(f"Erro ao cadastrar perfil: {e}")
            return jsonify(success=False, mensagem="Erro ao cadastrar perfil.")

    return render_template('add_profile.html')

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

@app.route('/search_user', methods=['GET'])
def search_user():
    query = request.args.get('query', '').strip()
    
    if query:
        users = User.query.join(Profile).filter(
            (User.nome.ilike(f'%{query}%')) |
            (User.email.ilike(f'%{query}%')) |
            (Profile.name.ilike(f'%{query}%'))
        ).all()
    else:
        users = User.query.options(joinedload(User.profile)).all()  # Carrega todos os usuários se não houver busca

    return render_template('partials/user_table.html', users=users)

@app.route('/delete_user', methods=['POST'])
def delete_user():
    user_id = request.form['user_id']
    
    PasswordResetToken.query.filter_by(user_id=user_id).delete()
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    return {'status': 'success'}, 200

@app.route('/search_profile', methods=['GET'])
def search_profile():
    query = request.args.get('query', '').strip()

    if query:
        profiles = Profile.query.filter(Profile.name.ilike(f'%{query}%')).all()
    else:
        profiles = Profile.query.all()  # Carrega todos os perfis se não houver busca

    return render_template('partials/profile_table.html', profiles=profiles)

@app.route('/edit_profile/<int:id>', methods=['GET', 'POST'])
def edit_profile(id):
    profile = Profile.query.get_or_404(id)
    if request.method == 'POST':
        profile.name = request.form['profile_name']
        db.session.commit()
        flash('Perfil atualizado com sucesso!')
        return jsonify(status='success')  # Retorna um JSON de sucesso

    return render_template('partials/edit_profile.html', profile=profile)

@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    profile_id = request.form['profile_id']
    profile = Profile.query.get_or_404(profile_id)
    db.session.delete(profile)
    db.session.commit()
    return {'status': 'success'}, 200

@app.route('/consultar_perfil', methods=['GET'])
def consultar_perfil():
    query = request.args.get('query', '').strip()

    if query:
        profiles = Profile.query.filter(Profile.name.ilike(f'%{query}%')).all()
    else:
        profiles = Profile.query.all()

    return render_template('partials/consultar_perfil.html', profiles=profiles)

@app.route('/principal')
def principal():
    return render_template('principal.html')

# Atualizar Relatórios do Fiplan
@app.route('/executar_fip613', methods=['GET', 'POST'])
@login_required
def executar_fip613():
    # Obtém o registro mais recente com base na data de atualização
    latest_entry = db.session.query(Fip613).order_by(Fip613.data_atualizacao.desc()).first()
    
    # Extrai informações de data e usuário, se o registro existir
    latest_data_arquivo = latest_entry.data_arquivo if latest_entry else None
    latest_data_atualizacao = latest_entry.data_atualizacao if latest_entry else None
    latest_user = latest_entry.user.nome if latest_entry and latest_entry.user else 'Usuário desconhecido'

    if request.method == 'POST':
        if 'file' not in request.files or 'manualModifiedDate' not in request.form:
            return jsonify(success=False, mensagem='Arquivo ou data de modificação não selecionados.')

        file = request.files['file']
        if file.filename == '':
            return jsonify(success=False, mensagem='Nenhum arquivo selecionado.')

        # Obtenha a data de modificação do formulário
        manual_modified_date_str = request.form['manualModifiedDate']
        try:
            data_arquivo = datetime.fromisoformat(manual_modified_date_str)
        except ValueError:
            return jsonify(success=False, mensagem='Data de modificação inválida.')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                # Salva o arquivo
                file.save(file_path)

                # Converte a data e hora local para o fuso horário UTC-4 antes de enviar para o banco
                data_atualizacao_local = datetime.now(local_timezone)

                # Processa o arquivo carregado com a data de atualização e o ID do usuário logado
                run_fip613(file_path, data_arquivo, db, user_id=current_user.id, data_atualizacao=data_atualizacao_local)

                # Retorna resposta JSON para exibir modal de confirmação
                return jsonify(success=True, mensagem='Relatório FIP 613 atualizado com sucesso!')
            except Exception as e:
                print(f"Erro ao salvar ou processar o arquivo: {e}")
                return jsonify(success=False, mensagem=f'Erro ao processar o arquivo: {e}')

    return render_template(
        'partials/atualizar_fip613.html',
        latest_data_arquivo=latest_data_arquivo,
        latest_data_atualizacao=latest_data_atualizacao,
        latest_user=latest_user
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'xlsx'


@app.route('/iniciar_fip613', methods=['POST'])
@login_required
def iniciar_fip613():
    try:
        run_fip613()
        mensagem = "Relatório FIP 613 atualizado com sucesso!"
        return jsonify(success=True, mensagem=mensagem)
    except Exception as e:
        print(f"Erro ao executar o script: {e}")
        return jsonify(success=False, mensagem=f"Erro ao executar o script: {e}")

@app.route('/pagina_confirmacao')
def pagina_confirmacao():
    return render_template('partials/pagina_confirmacao.html', mensagem="Registro gravado com sucesso!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)