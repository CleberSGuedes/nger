import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import numpy as np
import logging

# Configurações de blocos para processamento
BATCH_SIZE = 1000  # Tamanho dos blocos principais
SUB_BATCH_SIZE = 100  # Tamanho dos sublotes menores

# Configura o logger do SQLAlchemy para exibir apenas avisos e erros
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def process_ped_file(file_path, manual_date, user_id, data_atualizacao):
    """
    Processa o arquivo PED e insere/atualiza registros no banco de dados em blocos e sub-blocos.

    Args:
        file_path (str): Caminho do arquivo Excel.
        manual_date (datetime): Data manual informada pelo usuário.
        user_id (int): ID do usuário que está atualizando os dados.
        data_atualizacao (datetime): Data e hora da atualização.

    Returns:
        int: Total de registros inseridos ou atualizados no banco.
    """
    print("Carregando o arquivo PED...")

    # Carrega o Excel e define o cabeçalho
    df = pd.read_excel(file_path, header=None)
    print("✅ Arquivo carregado com sucesso.")

    # Encontra a linha do cabeçalho e ajusta os nomes das colunas
    header_row = df[df.iloc[:, 0] == "Exercício"].index[0]
    df.columns = df.iloc[header_row].values  # Define os nomes das colunas
    df = df[header_row + 1:].reset_index(drop=True)

    # Mapeamento das colunas do Excel para as colunas do banco de dados
    column_mapping = {
        "Exercício": "exercicio",
        "Nº PED": "num_ped",
        "Nº PED Estorno/Estornado": "num_ped_estorno_estornado",
        "Nº EMP": "num_emp",
        "Nº CAD": "num_cad",
        "Nº NOBLIST": "num_noblist",
        "Nº DOTLIST": "num_dotlist",
        "Nº OS": "num_os",
        "Convênio": "convenio",
        "Nº Processo Orçamentário de Pagamento": "num_processo_orcamentario_pagamento",
        "Valor PED": "valor_ped",
        "Valor do Estorno": "valor_estorno",
        "Indicativo de Licitação de Exercícios Anteriores": "indicativo_licitacao_exercicios_anteriores",
        "Data da Licitação": "data_licitacao",
        "Liberado Fisco Estadual": "liberado_fisco_estadual",
        "Situação": "situacao",
        "UO": "uo",
        "Nome da Unidade Orçamentária": "nome_unidade_orcamentaria",
        "UG": "ug",
        "Nome da Unidade Gestora": "nome_unidade_gestora",
        "Data Solicitação": "data_solicitacao",
        "Data Criação": "data_criacao",
        "Tipo Empenho": "tipo_empenho",
        "Dotação Orçamentária": "dotacao_orcamentaria",
        "Nº Emenda (EP)": "num_emenda_ep",
        "Autor da Emenda (EP)": "autor_emenda_ep",
        "Elemento": "elemento",
        "Nome do Elemento": "nome_elemento",
        "Nº CAC": "num_cac",
        "Licitação": "licitacao",
        "Histórico": "historico",
        "Data Autorização": "data_autorizacao",
        "Data/Hora Cadastro Autorização": "data_hora_cadastro_autorizacao",
        "Credor": "credor",
        "Nome do Credor": "nome_credor",
        "Tipo de Despesa": "tipo_despesa",
        "Nº ABJ": "num_abj",
        "Nº Processo do Sequestro Judicial": "num_processo_sequestro_judicial",
        "Indicativo de Entrega imediata - § 4º  Art. 62 Lei 8.666": "indicativo_entrega_imediata",
        "Indicativo de contrato": "indicativo_contrato",
        "Código UO Extinta": "codigo_uo_extinta",
        "Devolução GCV": "devolucao_gcv",
        "Mês de Competência da Folha de Pagamento": "mes_competencia_folha_pagamento",
        "Exercício de Competência da Folha de Pagamento": "exercicio_competencia_folha_pagamento",
        "Obrigação Patronal": "obrigacao_patronal",
        "Tipo de Obrigação Patronal": "tipo_obrigacao_patronal",
        "Nº NLA": "num_nla",
    }

    # Renomeia as colunas conforme o mapeamento
    df.rename(columns=column_mapping, inplace=True)
    expected_columns = list(column_mapping.values())
    df = df[[col for col in expected_columns if col in df.columns]]

    # Adiciona colunas de controle
    df['data_arquivo'] = manual_date
    df['data_atualizacao'] = data_atualizacao
    df['user_id'] = user_id

    # Preencher valores ausentes e corrigir formatação de colunas
    for col in df.columns:
        if 'data' in col.lower():  # Verifica colunas que contêm 'data' no nome
            df[col] = pd.to_datetime(df[col], errors='coerce')  # Converte valores inválidos para NaT
            df[col] = df[col].fillna('1900-01-01 00:00:00')  # Substitui NaT por data padrão válida
        elif pd.api.types.is_numeric_dtype(df[col]):  # Para colunas numéricas
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)  # Substitui NaN por 0
        elif pd.api.types.is_object_dtype(df[col]):  # Para colunas de texto
            df[col] = df[col].replace({np.nan: None, "": None, "NaT": None})  # Substitui valores ausentes por None
        else:  # Para outros tipos de dados
            df[col] = df[col].fillna(None)  # Substitui valores ausentes por None

    # Ajuste de formatação para colunas do tipo DATETIME no MySQL
    for col in df.columns:
        if 'data' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

    # Conexão com o banco de dados
    engine = create_engine(
        'mysql+pymysql://root:OXRlbi29015@177.87.122.164:3306/sistemanger',
        isolation_level="AUTOCOMMIT",
        echo=False
    )

    total_records = 0
    print("Iniciando inserção em blocos...")

    try:
        with engine.connect() as conn:
            for block_start in range(0, len(df), BATCH_SIZE):
                block = df.iloc[block_start:block_start + BATCH_SIZE]

                for sub_start in range(0, len(block), SUB_BATCH_SIZE):
                    sub_batch = block.iloc[sub_start:sub_start + SUB_BATCH_SIZE]
                    placeholders = ", ".join([f":{col}" for col in df.columns])
                    sql = f"""
                    INSERT INTO ped ({', '.join(df.columns)})
                    VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE
                    data_atualizacao = VALUES(data_atualizacao);
                    """
                    conn.execute(text(sql), sub_batch.to_dict(orient="records"))
                    total_records += len(sub_batch)
                    print(f"✅ Sub-bloco de {len(sub_batch)} registros inseridos/atualizados.")

                print(f"✅ Bloco de {len(block)} registros processados.")

        print(f"✅ Processamento concluído. Total de registros inseridos/atualizados: {total_records}")

    except SQLAlchemyError as e:
        print(f"❌ Erro durante o processamento: {e}")
        raise
    finally:
        engine.dispose()

    return total_records
