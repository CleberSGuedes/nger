# user.py
from sqlalchemy.orm import Session
from .models import Usuario

def cadastrar_usuario(db: Session, nome: str, senha: str):
    """Cadastra um novo usuário no banco de dados."""
    novo_usuario = Usuario(nome=nome, senha=senha)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

def verifica_usuario(db: Session, nome: str, senha: str) -> bool:
    """Verifica se as credenciais do usuário estão corretas."""
    usuario = db.query(Usuario).filter(Usuario.nome == nome, Usuario.senha == senha).first()
    return usuario is not None
