# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configurações do banco de dados
DATABASE_URL = "mysql+pymysql://root:guedes90@127.0.0.1:3306/sistemanger"

# Cria o motor e a sessão
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def get_db_session():
    """Obtém uma nova sessão do banco de dados."""
    return Session()
