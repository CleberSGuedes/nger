# models.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    senha = Column(String, nullable=False)
    email = Column(String(255), nullable=False, unique=True)  # Adicionado campo de e-mail
    perfil_id = Column(Integer, ForeignKey('perfis.id'))
    
    perfil = relationship("Perfil")

class Perfil(Base):
    __tablename__ = 'perfis'
    id = Column(Integer, primary_key=True)
    nome = Column(String(50), nullable=False)
    nivel_acesso = Column(Integer, nullable=False)
