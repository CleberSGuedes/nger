from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Text, DECIMAL, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  # Importando UserMixin
from datetime import datetime


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
    uo = Column(String(10), nullable=True)
    ug = Column(String(10), nullable=True)
    funcao = Column(String(100), nullable=True)
    subfuncao = Column(String(250), nullable=True)
    programa = Column(String(250), nullable=True)
    projeto_atividade = Column(String(500), nullable=True)
    regional = Column(String(50), nullable=True)
    natureza_despesa = Column(String(30), nullable=True)
    fonte_recurso = Column(String(30), nullable=True)
    iduso = Column(Integer, nullable=True)
    tipo_recurso = Column(String(50), nullable=True)
    dotacao_inicial = Column(Float, nullable=True)
    cred_suplementar = Column(Float, nullable=True)
    cred_especial = Column(Float, nullable=True)
    cred_extraordinario = Column(Float, nullable=True)
    reducao = Column(Float, nullable=True)
    cred_autorizado = Column(Float, nullable=True)
    bloqueado_conting = Column(Float, nullable=True)
    reserva_empenho = Column(Float, nullable=True)
    saldo_destaque = Column(Float, nullable=True)
    saldo_dotacao = Column(Float, nullable=True)
    empenhado = Column(Float, nullable=True)
    liquidado = Column(Float, nullable=True)
    a_liquidar = Column(Float, nullable=True)
    valor_pago = Column(Float, nullable=True)
    valor_a_pagar = Column(Float, nullable=True)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ano = Column(Integer, nullable=True)
    data_arquivo = Column(DateTime)  # Coluna para armazenar a data de criação do arquivo

class Ped(Base):
    __tablename__ = 'ped'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Chave primária
    exercicio = Column(Integer, nullable=True)
    num_ped = Column(String(50), nullable=True)
    num_ped_estorno_estornado = Column(String(50), nullable=True)
    num_emp = Column(String(50), nullable=True)
    num_cad = Column(String(50), nullable=True)
    num_noblist = Column(String(50), nullable=True)
    num_dotlist = Column(String(50), nullable=True)
    num_os = Column(String(50), nullable=True)
    convenio = Column(String(50), nullable=True)
    num_processo_orcamentario_pagamento = Column(String(50), nullable=True)
    valor_ped = Column(DECIMAL(15, 2), nullable=True)
    valor_estorno = Column(DECIMAL(15, 2), nullable=True)
    indicativo_licitacao_exercicios_anteriores = Column(String(10), nullable=True)
    data_licitacao = Column(Date, nullable=True)
    liberado_fisco_estadual = Column(String(10), nullable=True)
    situacao = Column(String(500), nullable=True)
    uo = Column(String(50), nullable=True)
    nome_unidade_orcamentaria = Column(String(200), nullable=True)
    ug = Column(String(50), nullable=True)
    nome_unidade_gestora = Column(String(200), nullable=True)
    data_solicitacao = Column(Date, nullable=True)
    data_criacao = Column(Date, nullable=True)
    tipo_empenho = Column(String(50), nullable=True)
    dotacao_orcamentaria = Column(Text, nullable=True)
    num_emenda_ep = Column(String(50), nullable=True)
    autor_emenda_ep = Column(String(200), nullable=True)
    elemento = Column(String(50), nullable=True)
    nome_elemento = Column(String(200), nullable=True)
    num_cac = Column(String(50), nullable=True)
    licitacao = Column(String(50), nullable=True)
    historico = Column(Text, nullable=True)
    data_autorizacao = Column(Date, nullable=True)
    data_hora_cadastro_autorizacao = Column(DateTime, nullable=True)
    credor = Column(String(100), nullable=True)
    nome_credor = Column(String(250), nullable=True)
    tipo_despesa = Column(String(100), nullable=True)
    num_abj = Column(String(50), nullable=True)
    num_processo_sequestro_judicial = Column(String(50), nullable=True)
    indicativo_entrega_imediata = Column(String(10), nullable=True)
    indicativo_contrato = Column(String(10), nullable=True)
    codigo_uo_extinta = Column(String(50), nullable=True)
    devolucao_gcv = Column(String(10), nullable=True)
    mes_competencia_folha_pagamento = Column(String(50), nullable=True)
    exercicio_competencia_folha_pagamento = Column(Integer, nullable=True)
    obrigacao_patronal = Column(String(50), nullable=True)
    tipo_obrigacao_patronal = Column(String(50), nullable=True)
    num_nla = Column(String(50), nullable=True)
    data_atualizacao = Column(DateTime, nullable=True)
    data_arquivo = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)