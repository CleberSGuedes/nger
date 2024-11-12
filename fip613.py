import os
import pandas as pd
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

# Configuração SFTP para transferir o arquivo
sftp_host = "seu_servidor.com"
sftp_port = 22
sftp_username = "seu_usuario"
sftp_password = "sua_senha"
remote_folder_path = "/caminho/no/servidor"

# Define o diretório e caminho absoluto para o arquivo de saída
output_directory = os.path.join(os.getcwd(), "outputs")  # Usa uma pasta "outputs" para organizar melhor
output_path = os.path.join(output_directory, "fip613_limped.xlsx")
BATCH_SIZE = 80

# Função para garantir que o diretório de saída existe
def ensure_output_directory():
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Diretório de saída criado em: {output_directory}")

# Garante que o diretório seja criado no início
ensure_output_directory()

def get_file_creation_date(file_path):
    """Obtém a data e hora de criação do arquivo."""
    creation_time = os.path.getctime(file_path)
    return datetime.fromtimestamp(creation_time)

def get_year_from_file(file_path, sheet_name="FIPLAN"):
    """Obtém o ano da planilha com base na linha contendo 'Exercício igual a'."""
    try:
        raw_data = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        for _, row in raw_data.iterrows():
            for cell in row:
                if isinstance(cell, str) and "Exercício igual a" in cell:
                    year = int(cell.split()[-1])
                    print(f"Ano encontrado: {year}")
                    return year
    except Exception as e:
        print(f"Erro ao obter o ano: {e}")
    return None

def load_clean_data(file_path, sheet_name="FIPLAN"):
    """Carrega e limpa os dados do arquivo Excel especificado."""
    print("Carregando e limpando dados da planilha...")
    raw_data = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    
    header_row_index = None
    for i, row in raw_data.iterrows():
        if 'UO' in row.values and 'UG' in row.values:
            header_row_index = i
            break
    
    if header_row_index is not None:
        data = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row_index)
        data = data.dropna(how='all').reset_index(drop=True)
        data = data.dropna(subset=['UO', 'UG', 'Função', 'Subfunção', 'Programa', 'Projeto/Atividade'])
        
        total_row_index = data[data.apply(lambda row: row.astype(str).str.contains("Total UO 14101").any(), axis=1)].index
        if not total_row_index.empty:
            data = data.iloc[:total_row_index[0]]
        
        print(f"Registros válidos lidos: {len(data)}")
        
        data.rename(columns={
            "UO": "uo",
            "UG": "ug",
            "Função": "funcao",
            "Subfunção": "subfuncao",
            "Programa": "programa",
            "Projeto/Atividade": "projeto_atividade",
            "Regional": "regional",
            "Natureza de Despesa": "natureza_despesa",
            "Fonte de Recurso": "fonte_recurso",
            "Iduso": "iduso",
            "Tipo de Recurso": "tipo_recurso",
            "Dotação Inicial": "dotacao_inicial",
            "Créd. Suplementar": "cred_suplementar",
            "Créd. Especial": "cred_especial",
            "Créd. Extraordinário": "cred_extraordinario",
            "Redução": "reducao",
            "Créd. Autorizado": "cred_autorizado",
            "Bloqueado/Conting.": "bloqueado_conting",
            "Reserva Empenho": "reserva_empenho",
            "Saldo de Destaque": "saldo_destaque",
            "Saldo Dotação": "saldo_dotacao",
            "Empenhado": "empenhado",
            "Liquidado": "liquidado",
            "A liquidar": "a_liquidar",
            "Valor Pago": "valor_pago",
            "Valor a Pagar": "valor_a_pagar"
        }, inplace=True)
        
        numeric_columns = [
            "dotacao_inicial", "cred_suplementar", "cred_especial", "cred_extraordinario", "reducao",
            "cred_autorizado", "bloqueado_conting", "reserva_empenho", "saldo_destaque",
            "saldo_dotacao", "empenhado", "liquidado", "a_liquidar", "valor_pago", "valor_a_pagar"
        ]
        
        for col in numeric_columns:
            data[col] = data[col].astype(str).str.replace('.', '', regex=False)
            data[col] = data[col].str.replace(',', '.', regex=False).astype(float)
        
        data['iduso'] = pd.to_numeric(data['iduso'], errors='coerce').fillna(0).astype(int)
        
        return data
    else:
        print("Cabeçalho não encontrado na planilha.")
        return None

def save_clean_data(data, output_path):
    """Salva os dados limpos em um novo arquivo Excel."""
    try:
        ensure_output_directory()  # Garante que o diretório exista antes de salvar
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"Arquivo existente {output_path} removido.")
        
        data.to_excel(output_path, index=False)
        print(f"Arquivo limpo salvo em: {output_path}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo limpo: {e}")

def update_database(data, ano, data_arquivo, db, user_id, data_atualizacao):
    registros_gravados = 0
    print("Iniciando inserção dos registros no banco de dados em lotes...")

    db.session.execute(text("TRUNCATE TABLE fip613"))
    db.session.commit()
    print("Tabela fip613 truncada devido à nova data de modificação do arquivo.")

    for start in range(0, len(data), BATCH_SIZE):
        batch_data = data.iloc[start:start + BATCH_SIZE]
        for _, row in batch_data.iterrows():
            try:
                row['data_atualizacao'] = data_atualizacao  # Usa a string para o horário local
                row['ano'] = ano
                row['data_arquivo'] = data_arquivo
                row['user_id'] = user_id
                db.session.execute(text("""
                    INSERT INTO fip613 (
                        uo, ug, funcao, subfuncao, programa, projeto_atividade, regional, natureza_despesa,
                        fonte_recurso, iduso, tipo_recurso, dotacao_inicial, cred_suplementar, cred_especial,
                        cred_extraordinario, reducao, cred_autorizado, bloqueado_conting, reserva_empenho,
                        saldo_destaque, saldo_dotacao, empenhado, liquidado, a_liquidar, valor_pago,
                        valor_a_pagar, data_atualizacao, ano, data_arquivo, user_id
                    ) VALUES (
                        :uo, :ug, :funcao, :subfuncao, :programa, :projeto_atividade, :regional, :natureza_despesa,
                        :fonte_recurso, :iduso, :tipo_recurso, :dotacao_inicial, :cred_suplementar, :cred_especial,
                        :cred_extraordinario, :reducao, :cred_autorizado, :bloqueado_conting, :reserva_empenho,
                        :saldo_destaque, :saldo_dotacao, :empenhado, :liquidado, :a_liquidar, :valor_pago,
                        :valor_a_pagar, :data_atualizacao, :ano, :data_arquivo, :user_id
                    )
                    ON DUPLICATE KEY UPDATE
                        funcao = VALUES(funcao),
                        subfuncao = VALUES(subfuncao),
                        programa = VALUES(programa),
                        projeto_atividade = VALUES(projeto_atividade),
                        regional = VALUES(regional),
                        natureza_despesa = VALUES(natureza_despesa),
                        fonte_recurso = VALUES(fonte_recurso),
                        iduso = VALUES(iduso),
                        tipo_recurso = VALUES(tipo_recurso),
                        dotacao_inicial = VALUES(dotacao_inicial),
                        cred_suplementar = VALUES(cred_suplementar),
                        cred_especial = VALUES(cred_especial),
                        cred_extraordinario = VALUES(cred_extraordinario),
                        reducao = VALUES(reducao),
                        cred_autorizado = VALUES(cred_autorizado),
                        bloqueado_conting = VALUES(bloqueado_conting),
                        reserva_empenho = VALUES(reserva_empenho),
                        saldo_destaque = VALUES(saldo_destaque),
                        saldo_dotacao = VALUES(saldo_dotacao),
                        empenhado = VALUES(empenhado),
                        liquidado = VALUES(liquidado),
                        a_liquidar = VALUES(a_liquidar),
                        valor_pago = VALUES(valor_pago),
                        valor_a_pagar = VALUES(valor_a_pagar),
                        data_atualizacao = :data_atualizacao,
                        ano = :ano,
                        data_arquivo = :data_arquivo,
                        user_id = :user_id
                """), row.to_dict())
                
                registros_gravados += 1
            except SQLAlchemyError as e:
                print(f"Erro ao inserir o registro: {str(e)}")
        
        db.session.commit()
        print(f"{len(batch_data)} registros gravados no banco de dados no lote atual.")
    
    print(f"Total de registros gravados: {registros_gravados}")

def run_fip613(file_path, data_arquivo, db, user_id, data_atualizacao):
    ano = get_year_from_file(file_path)
    data = load_clean_data(file_path)
    
    if data is not None and ano is not None:
        save_clean_data(data, output_path)
        cleaned_data = pd.read_excel(output_path)
        update_database(cleaned_data, ano, data_arquivo, db, user_id, data_atualizacao)
    else:
        print("Erro: Não foi possível carregar dados limpos da planilha.")
