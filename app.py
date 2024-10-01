# app.py
import streamlit as st
from .database import get_db_session
from .user import cadastrar_usuario, verifica_usuario

# Inicializa a sessão
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.usuario = None

# Título da aplicação
st.title("Sistema NGER SEDUC-MT")

# Conexão com o banco de dados
db_session = get_db_session()

# Campos de entrada para o login
if not st.session_state.logged_in:
    usuario = st.text_input("Nome de Usuário")
    senha = st.text_input("Senha", type="password")

    # Botão de login
    if st.button("Entrar"):
        if verifica_usuario(db_session, usuario, senha):
            st.session_state.logged_in = True
            st.session_state.usuario = usuario  # Armazena o nome de usuário na sessão
            st.success("Login bem-sucedido!")
        else:
            st.error("Nome de usuário ou senha incorretos.")
else:
    # Acesso à interface do sistema
    st.success(f"Bem-vindo, {st.session_state.usuario}!")

    # Menu de opções
    option = st.selectbox("Menu", ["Cadastro de Usuários", "Fluxo de Caixa", "Atualizar Tabelas"])

    if option == "Cadastro de Usuários":
        st.subheader("Cadastrar Usuário")
        novo_usuario = st.text_input("Novo Nome de Usuário")
        nova_senha = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar"):
            cadastrar_usuario(db_session, novo_usuario, nova_senha)
            st.success("Usuário cadastrado com sucesso!")

    elif option == "Fluxo de Caixa":
        st.subheader("Gerenciar Fluxo de Caixa")
        # Lógica para gerenciar fluxo de caixa vai aqui

    elif option == "Atualizar Tabelas":
        st.subheader("Atualizar Tabelas")
        uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx", "xls"])
        if uploaded_file is not None:
            import pandas as pd
            df = pd.read_excel(uploaded_file)
            st.write(df)  # Mostra o dataframe carregado
