from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  # Importando UserMixin

Base = declarative_base()

class User(Base, UserMixin):  # Adicionando UserMixin
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

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
