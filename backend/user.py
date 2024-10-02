# user.py
import smtplib
from sqlalchemy.orm import Session
from models import Usuario, Perfil
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurações do servidor SMTP
SMTP_SERVER = 'smtp.gmail.com'  # Servidor SMTP do Gmail
SMTP_PORT = 587  # Porta para servidores de e-mail
EMAIL_ADDRESS = 'cleber.guedes@edu.mt.gov.br'  # Seu e-mail
EMAIL_PASSWORD = 'wgno zsyk maku vnjp'  # Sua senha ou senha de aplicativo

def enviar_email(destinatario: str, nova_senha: str):
    """Envia um e-mail com a nova senha para o usuário."""
    mensagem = MIMEMultipart()
    mensagem['From'] = EMAIL_ADDRESS
    mensagem['To'] = destinatario
    mensagem['Subject'] = 'Redefinição de Senha'

    corpo_mensagem = f'Sua nova senha temporária é: {nova_senha}'
    mensagem.attach(MIMEText(corpo_mensagem, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as servidor:
            servidor.starttls()  # Estabelece uma conexão segura
            servidor.login(EMAIL_ADDRESS, EMAIL_PASSWORD)  # Realiza o login
            servidor.send_message(mensagem)  # Envia o e-mail
            print(f'E-mail enviado para {destinatario}')
    except Exception as e:
        print(f'Erro ao enviar e-mail: {e}')

def cadastrar_usuario(db: Session, nome: str, senha: str, email: str, perfil_id: int):
    """Cadastra um novo usuário no banco de dados associado a um perfil."""
    novo_usuario = Usuario(nome=nome, senha=senha, email=email, perfil_id=perfil_id)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

def verificar_usuario(db: Session, nome: str, senha: str) -> bool:
    """Verifica se as credenciais do usuário estão corretas."""
    usuario = db.query(Usuario).filter(Usuario.nome == nome, Usuario.senha == senha).first()
    return usuario is not None

def buscar_perfis(db: Session):
    """Busca todos os perfis do banco de dados."""
    return db.query(Perfil).all()

def cadastrar_perfil(db: Session, nome: str, nivel_acesso: int):
    """Cadastra um novo perfil no banco de dados."""
    novo_perfil = Perfil(nome=nome, nivel_acesso=nivel_acesso)
    db.add(novo_perfil)
    db.commit()
    db.refresh(novo_perfil)
    return novo_perfil

def buscar_usuario_por_email(db: Session, email: str):
    """Busca um usuário pelo e-mail."""
    return db.query(Usuario).filter(Usuario.email == email).first()

def gerar_senha_temporaria(length=8):
    """Gera uma senha temporária aleatória."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def atualizar_senha(db: Session, usuario: Usuario, nova_senha: str):
    """Atualiza a senha do usuário."""
    usuario.senha = nova_senha
    db.commit()
