import os
import paramiko
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

# Caminho de saída do arquivo processado
output_path = "fip613_limped.xlsx"

def get_latest_file(folder_path):
    """Encontra o arquivo mais recente no diretório especificado."""
    files = [f for f in os.listdir(folder_path) if f.endswith('.xlsx') and not f.startswith('~$')]
    paths = [os.path.join(folder_path, f) for f in files]
    latest_file = max(paths, key=os.path.getmtime)
    print(f"Arquivo mais recente encontrado: {latest_file}")
    return latest_file

def transfer_file_to_server(local_file, remote_path):
    """Transfere um arquivo local para o servidor via SFTP."""
    try:
        print("Conectando ao servidor SFTP...")
        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.connect(username=sftp_username, password=sftp_password)

        sftp = paramiko.SFTPClient.from_transport(transport)
        remote_file_path = os.path.join(remote_path, os.path.basename(local_file))
        sftp.put(local_file, remote_file_path)

        print(f"Arquivo {local_file} transferido para {remote_file_path} no servidor.")
        sftp.close()
        transport.close()
    except Exception as e:
        print(f"Erro ao transferir o arquivo para o servidor: {e}")

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
        
        # Renomear colunas para garantir que correspondam aos nomes dos parâmetros SQL
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
        
        # Converter colunas com valores monetários do formato brasileiro para numérico
        numeric_columns = [
            "dotacao_inicial", "cred_suplementar", "cred_especial", "cred_extraordinario", "reducao",
            "cred_autorizado", "bloqueado_conting", "reserva_empenho", "saldo_destaque",
            "saldo_dotacao", "empenhado", "liquidado", "a_liquidar", "valor_pago", "valor_a_pagar"
        ]
        
        for col in numeric_columns:
            data[col] = data[col].astype(str).str.replace('.', '', regex=False)
            data[col] = data[col].str.replace(',', '.', regex=False).astype(float)
        
        # Converter 'iduso' para inteiro
        data['iduso'] = pd.to_numeric(data['iduso'], errors='coerce').fillna(0).astype(int)
        
        return data
    else:
        print("Cabeçalho não encontrado na planilha.")
        return None

def save_clean_data(data, output_path):
    """Salva os dados limpos em um novo arquivo Excel."""
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"Arquivo existente {output_path} removido.")
        
        data.to_excel(output_path, index=False)
        print(f"Arquivo limpo salvo em: {output_path}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo limpo: {e}")

def update_database(data):
    """Insere os dados no banco de dados."""
    from app import db, app
    with app.app_context():
        registros_gravados = 0
        print("Iniciando inserção dos registros no banco de dados...")
        
        for i, row in data.iterrows():
            try:
                row['data_atualizacao'] = datetime.now()
                db.session.execute(text("""
                    INSERT INTO fip613 (
                        uo, ug, funcao, subfuncao, programa, projeto_atividade, regional, natureza_despesa,
                        fonte_recurso, iduso, tipo_recurso, dotacao_inicial, cred_suplementar, cred_especial,
                        cred_extraordinario, reducao, cred_autorizado, bloqueado_conting, reserva_empenho,
                        saldo_destaque, saldo_dotacao, empenhado, liquidado, a_liquidar, valor_pago,
                        valor_a_pagar, data_atualizacao
                    ) VALUES (
                        :uo, :ug, :funcao, :subfuncao, :programa, :projeto_atividade, :regional, :natureza_despesa,
                        :fonte_recurso, :iduso, :tipo_recurso, :dotacao_inicial, :cred_suplementar, :cred_especial,
                        :cred_extraordinario, :reducao, :cred_autorizado, :bloqueado_conting, :reserva_empenho,
                        :saldo_destaque, :saldo_dotacao, :empenhado, :liquidado, :a_liquidar, :valor_pago,
                        :valor_a_pagar, :data_atualizacao
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
                        data_atualizacao = :data_atualizacao
                """), row.to_dict())
                
                registros_gravados += 1
                print(f"Registro {i + 1} gravado com sucesso.")
            except SQLAlchemyError as e:
                print(f"Erro ao inserir o registro na linha {i + 1}: {str(e)}")
        
        db.session.commit()
        print(f"Registros processados: {len(data)}, Registros gravados: {registros_gravados}")
        if registros_gravados == 0:
            print("Aviso: Nenhum registro foi gravado no banco de dados.")

def run_fip613(file_path):
    """Função principal para executar todo o processo de atualização dos dados a partir de um arquivo fornecido."""
    data = load_clean_data(file_path)
    
    if data is not None:
        save_clean_data(data, output_path)
        cleaned_data = pd.read_excel(output_path)
        update_database(cleaned_data)
    else:
        print("Erro: Não foi possível carregar dados limpos da planilha.")
