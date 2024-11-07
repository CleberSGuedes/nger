from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  # Importando UserMixin

Base = declarative_base()

class User(Base, UserMixin):  # Adicionando UserMixin
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)  # Adicionando o campo nome
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_active(self):
        return True  # Você pode implementar lógica adicional, se necessário

    def is_authenticated(self):
        return True  # Já está definido no UserMixin

    def is_anonymous(self):
        return False  # Já está definido no UserMixin

class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'
    
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    expiration_time = Column(DateTime, nullable=False)  # Campo de expiração

    user = relationship('User', backref='reset_tokens')

class Fip613(Base):
    __tablename__ = 'fip613'

    id = Column(Integer, primary_key=True)
    uo = Column(Integer, nullable=False)
    ug = Column(Integer, nullable=False)
    funcao = Column(String(100))
    subfuncao = Column(String(500))
    programa = Column(String(500))
    projeto_atividade = Column(String(1000))
    regional = Column(String(100))
    natureza_despesa = Column(String(50))
    fonte_recurso = Column(String(50))
    iduso = Column(Integer)
    tipo_recurso = Column(String(50))
    dotacao_inicial = Column(Float)
    cred_suplementar = Column(Float)
    cred_especial = Column(Float)
    cred_extraordinario = Column(Float)
    reducao = Column(Float)
    cred_autorizado = Column(Float)
    bloqueado_conting = Column(Float)
    reserva_empenho = Column(Float)
    saldo_destaque = Column(Float)
    saldo_dotacao = Column(Float)
    empenhado = Column(Float)
    liquidado = Column(Float)
    a_liquidar = Column(Float)
    valor_pago = Column(Float)
    valor_a_pagar = Column(Float)
    data_atualizacao = Column(DateTime)  # Campo para armazenar a data de atualização mais recente
