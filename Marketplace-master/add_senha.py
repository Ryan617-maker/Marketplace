"""
Script para adicionar a coluna SENHA na tabela Cliente e definir senhas padrão.
Executar apenas UMA VEZ.
"""
import mysql.connector
from werkzeug.security import generate_password_hash

def add_senha_column():
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="0001",
        database="Marketplace"
    )
    cursor = conn.cursor()

    # Verificar se coluna já existe
    cursor.execute("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'Marketplace' AND TABLE_NAME = 'Cliente' AND COLUMN_NAME = 'SENHA'
    """)
    if cursor.fetchone()[0] == 0:
        cursor.execute("ALTER TABLE Cliente ADD COLUMN SENHA VARCHAR(255) DEFAULT NULL")
        print("Coluna SENHA adicionada com sucesso!")
    else:
        print("Coluna SENHA já existe.")

    # Atualizar senhas dos clientes existentes para "123456"
    senha_hash = generate_password_hash('123456')
    cursor.execute("UPDATE Cliente SET SENHA = %s WHERE SENHA IS NULL", (senha_hash,))
    conn.commit()

    cursor.execute("SELECT ID_CLIENTE, NOME, CPF FROM Cliente WHERE SENHA IS NOT NULL")
    clientes = cursor.fetchall()
    print(f"\nSenhas definidas para {len(clientes)} cliente(s):")
    for c in clientes:
        print(f"  Cliente #{c[0]}: {c[1]} ({c[2]}) - Senha: 123456")

    cursor.close()
    conn.close()
    print("\nPronto! Agora os clientes podem logar com CPF e senha 123456.")

if __name__ == "__main__":
    add_senha_column()
