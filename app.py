from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, PasswordResetToken  # Importar seu modelo User e PasswordResetToken
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
import os
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'guedes90'  # Mantenha isso em segredo!

# Configurando o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configurações do banco de dados
DATABASE_URL = "mysql+pymysql://root:guedes90@127.0.0.1:3306/sistemanger"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

@login_manager.user_loader
def load_user(user_id):
    return session.query(User).get(user_id)  # Obtém o usuário pelo ID

@app.route('/')
@login_required  # Apenas usuários logados podem acessar
def home():
    return render_template('home.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Verifique o usuário no banco de dados
        user = session.query(User).filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)  # Loga o usuário
            # flash('Login feito com sucesso!', 'success')
            return redirect(url_for('home'))
        else:
            flash('E-mail ou senha incorretos.', 'error')  # Mensagem de erro

    return render_template('login.html')

@app.route('/logout')
@login_required  # Apenas usuários logados podem acessar
def logout():
    logout_user()  # Loga o usuário
    flash('Você foi desconectado.', 'success')  # Mensagem de sucesso
    return redirect(url_for('login'))

# Configurações do Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'cleber.guedes@edu.mt.gov.br'  
app.config['MAIL_PASSWORD'] = 'wgno zsyk maku vnjp'  
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = session.query(User).filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(16)
            expiration_time = datetime.utcnow() + timedelta(hours=1)  # Define a validade do token

            # Armazenar o token e a data de expiração no banco de dados
            reset_token = PasswordResetToken(token=token, user_id=user.id, expiration_time=expiration_time)
            session.add(reset_token)
            session.commit()

            # Envia o e-mail com o link de redefinição
            msg = Message('Recuperação de Senha', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Acesse o link para redefinir sua senha: http://127.0.0.1:5000/reset-password/{token}'
            mail.send(msg)
            flash('E-mail de recuperação enviado!', 'success')
            return redirect(url_for('login'))
        else:
            flash('E-mail não encontrado.', 'error')  # Mensagem de erro
        
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_token = session.query(PasswordResetToken).filter_by(token=token).first()
    
    # Verifica se o token é inválido ou expirou
    if reset_token is None or reset_token.expiration_time < datetime.utcnow():
        flash('Token de redefinição inválido ou expirado.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        user = session.query(User).get(reset_token.user_id)

        if user:
            user.set_password(new_password)
            session.commit()  # Salvar a nova senha
            
            # Remover o token após o uso
            session.delete(reset_token)
            session.commit()

            flash('Senha redefinida com sucesso! Você pode fazer login agora.', 'success')
            return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        new_user = User(email=email)
        new_user.set_password(password)
        
        session.add(new_user)
        session.commit()  # Salva o usuário no banco de dados
        
        flash('Usuário registrado com sucesso! Você pode fazer login agora.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')  # Crie um template register.html

if __name__ == '__main__':
    app.run(debug=True)
