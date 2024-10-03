from flask import Flask, request, jsonify, render_template
from database import get_db_session
from user import (
    cadastrar_usuario,
    verificar_usuario,
    buscar_usuario_por_email,
    gerar_senha_temporaria,
    atualizar_senha,
)
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Carregar variáveis do arquivo .env
load_dotenv()

# Configurações do servidor SMTP
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Inicialização do Flask
app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')

# Função para enviar e-mail de redefinição de senha
def enviar_email(destinatario, nova_senha):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = destinatario
    msg['Subject'] = 'Redefinição de Senha'
    body = f'Sua nova senha é: {nova_senha}'
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f'E-mail enviado para {destinatario}')
    except Exception as e:
        print(f'Falha ao enviar e-mail: {e}')

# Rota para a página de login
@app.route('/', methods=['GET'])
def home():
    return render_template('login.html')  # Página de login

# Rota para a página "Esqueci a Senha"
@app.route('/esqueci-senha', methods=['GET'])
def esqueci_senha():
    return render_template('esqueci-senha.html')  # Página "Esqueci a Senha"

# Rota para processar login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usuario = data.get('usuario')
    senha = data.get('senha')

    if not usuario or not senha:
        return jsonify({"status": "error", "message": "Usuário e senha são obrigatórios."}), 400

    db_session = get_db_session()
    try:
        if verificar_usuario(db_session, usuario, senha):
            return jsonify({"status": "success", "message": "Login bem-sucedido!", "redirect": "/index"}), 200
        else:
            return jsonify({"status": "error", "message": "Nome de usuário ou senha incorretos."}), 401
    finally:
        db_session.close()

# Rota para a página inicial após o login
@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html')  # Página inicial

# Rota para registro de usuários
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    nome = data.get('nome')
    senha = data.get('senha')
    email = data.get('email')
    perfil_id = data.get('perfil_id')

    if not nome or not senha or not email or perfil_id is None:
        return jsonify({"status": "error", "message": "Todos os campos são obrigatórios."}), 400

    db_session = get_db_session()
    try:
        cadastrar_usuario(db_session, nome, senha, email, perfil_id)
        return jsonify({"status": "success", "message": "Usuário cadastrado!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db_session.close()

# Rota para enviar e-mail de redefinição de senha
@app.route('/send_email', methods=['POST'])
def send_email_route():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"status": "error", "message": "E-mail é obrigatório."}), 400

    nova_senha = gerar_senha_temporaria()
    db_session = get_db_session()
    try:
        usuario = buscar_usuario_por_email(db_session, email)
        if usuario:
            atualizar_senha(db_session, usuario, nova_senha)
            enviar_email(usuario.email, nova_senha)
            return jsonify({"status": "success", "message": "E-mail enviado!"}), 200
        else:
            return jsonify({"status": "error", "message": "Usuário não encontrado!"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db_session.close()

# Executa a aplicação Flask
if __name__ == '__main__':
    app.run(debug=True)
