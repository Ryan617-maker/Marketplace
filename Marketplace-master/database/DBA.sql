
CREATE DATABASE Marketplace;
USE Marketplace;

CREATE TABLE Cliente 
(
	ID_CLIENTE INT PRIMARY KEY AUTO_INCREMENT,
    NOME VARCHAR (50) NOT NULL,
    CPF CHAR(14) UNIQUE NOT NULL,
    DATA_NASCIMENTO DATE NOT NULL,
    SEXO ENUM ("Masculino", "Feminino") NOT NULL
);


CREATE TABLE Pedidos 
(
	ID_PEDIDO INT PRIMARY KEY AUTO_INCREMENT,
    DATA_PEDIDO DATE NOT NULL,
    VALOR_TOTAL DECIMAL (10,2) NOT NULL,
    STATUS ENUM('PENDENTE', 'PAGO', 'ENVIADO', 'ENTREGUE', 'CANCELADO') NOT NULL,
	ID_CLIENTE INT,
    FOREIGN KEY (ID_CLIENTE) REFERENCES Cliente (ID_CLIENTE)
);


CREATE TABLE CATEGORIA
(
	ID_CATEGORIA INT PRIMARY KEY AUTO_INCREMENT,
	NOME VARCHAR(50) NOT NULL
);



CREATE TABLE Produtos 
(
	ID_PRODUTO INT PRIMARY KEY AUTO_INCREMENT,
    NOME VARCHAR(30) NOT NULL,
	QUANTIDADE_DISPONIVEL INT NOT NULL,
    VALOR_UNITARIO DECIMAL(10,2) NOT NULL,
    ID_CATEGORIA INT,
    FOREIGN KEY (ID_CATEGORIA) REFERENCES CATEGORIA (ID_CATEGORIA) 
);
 
 
CREATE TABLE Estoque 
(
	ID_ESTOQUE INT PRIMARY KEY AUTO_INCREMENT,
	QUANTIDADE_ESTOQUE INT NOT NULL,
    LIMITE_MAXIMO INT NOT NULL,
    LIMITE_MINIMO INT NOT NULL,
	ID_PRODUTO INT ,
	FOREIGN KEY (ID_PRODUTO) REFERENCES Produtos (ID_PRODUTO)
);


CREATE TABLE Movimentacao 
(
	ID_MOVIMENTACAO INT PRIMARY KEY AUTO_INCREMENT,
    DATA_MOVIMENTACAO DATE NOT NULL,
	TIPO ENUM('ENTRADA', 'SAIDA') NOT NULL
);


CREATE TABLE Movimentacao_Produtos 
(
	ID_MOVIMENTACAO_PRODUTO INT PRIMARY KEY AUTO_INCREMENT,
    ID_MOVIMENTACAO INT,
    ID_PRODUTO INT,
    QUANTIDADE_MOVIMENTADA INT,
    FOREIGN KEY (ID_PRODUTO) REFERENCES Produtos (ID_PRODUTO),
    FOREIGN KEY (ID_MOVIMENTACAO) REFERENCES Movimentacao (ID_MOVIMENTACAO)
);


CREATE TABLE Pagamento 
(
    ID_PAGAMENTO INT PRIMARY KEY AUTO_INCREMENT,
    FORMA_PAGAMENTO ENUM( "PIX", "CARTAO_CREDITO", "CARTAO_DEBITO", "BOLETO") NOT NULL,
    VALOR_PAGO DECIMAL(10,2) NOT NULL,
    DATA_PAGAMENTO DATE NOT NULL,
    STATUS ENUM("PENDENTE", "APROVADO", "RECUSADO", "ESTORNADO" ) NOT NULL,
    ID_PEDIDO INT NOT NULL,
    FOREIGN KEY (ID_PEDIDO) REFERENCES Pedidos (ID_PEDIDO)
);


INSERT INTO Categoria (NOME) VALUES
("CARRO"),
("MOTO"), 
("CAMINHÃO"), 
("CARRETINHA");

INSERT INTO Cliente (NOME, CPF, DATA_NASCIMENTO, SEXO) VALUES
("Oliver Lucas Nathan Monteiro", "864.159.969-08", "1996-10-20", "Masculino"),
("Joana Emily Mariah Rodrigues", "553.986.544-89", "2002-12-25", "Feminino"),
("João Silva Dos Santos", "123.456.789-01", "1998-04-10", "Masculino");

INSERT INTO Produtos (NOME, QUANTIDADE_DISPONIVEL, VALOR_UNITARIO, ID_CATEGORIA)
VALUES
("Pneu Michelin Aro 17", 30, 650.00, 1),
("Capacete LS2", 20, 850.00, 2),
("Motor Diesel Volvo", 5, 28500.00, 3);

INSERT INTO Estoque (QUANTIDADE_ESTOQUE, LIMITE_MAXIMO, LIMITE_MINIMO, ID_PRODUTO)
VALUES
(30, 100, 10, 1), 
(20, 60, 5, 2), 
(5, 20, 2, 3);

INSERT INTO Movimentacao (DATA_MOVIMENTACAO, TIPO)
VALUES
("2026-07-01", "SAIDA"),
("2026-07-02", "SAIDA"),
("2026-07-03", "ENTRADA");

INSERT INTO Movimentacao_Produtos (ID_MOVIMENTACAO, ID_PRODUTO, QUANTIDADE_MOVIMENTADA)
VALUES
(1, 1, 30),
(2, 2, 16),
(3, 3, 28);

INSERT INTO Pedidos (DATA_PEDIDO, VALOR_TOTAL, STATUS, ID_CLIENTE)
VALUES
("2026-07-01", 1300.00, "PAGO", 1),
("2026-07-02", 850.00, "CANCELADO", 2),
("2026-07-03", 28500.00, "PENDENTE", 3);

INSERT INTO Pagamento (FORMA_PAGAMENTO, VALOR_PAGO, DATA_PAGAMENTO, STATUS, ID_PEDIDO)
VALUES
("PIX", 1300.00, "2026-07-01", "APROVADO", 1),
("BOLETO", 850.00, "2026-07-02", "RECUSADO", 2),
("CARTAO_CREDITO", 28500.00, "2026-07-03", "PENDENTE", 3);

SELECT * FROM Categoria;




# Lista os produtos junto com a categoria de cada um.
SELECT
P.NOME AS PRODUTO,                 -- Exibe o nome do produto
C.NOME AS CATEGORIA,               -- Exibe o nome da categoria
P.QUANTIDADE_DISPONIVEL,           -- Mostra a quantidade disponível
P.VALOR_UNITARIO                   -- Mostra o valor unitário
FROM Produtos P                    -- Tabela Produtos (apelido P)
INNER JOIN Categoria C             -- Faz a junção com a tabela Categoria
ON P.ID_CATEGORIA = C.ID_CATEGORIA;-- Relaciona produto e categoria pela chave estrangeira

# Lista os pedidos realizados por cada cliente.
SELECT
PE.ID_PEDIDO,                      -- Número do pedido
C.NOME,                            -- Nome do cliente
PE.DATA_PEDIDO,                    -- Data em que o pedido foi realizado
PE.VALOR_TOTAL,                    -- Valor total do pedido
PE.STATUS                          -- Situação do pedido
FROM Pedidos PE                    -- Tabela de pedidos
INNER JOIN Cliente C               -- Junta com a tabela Cliente
ON PE.ID_CLIENTE = C.ID_CLIENTE;   -- Relacionamento entre pedido e cliente

# Lista os pagamentos realizados pelos clientes.
SELECT
C.NOME,                            -- Nome do cliente
P.FORMA_PAGAMENTO,                 -- Forma de pagamento utilizada
P.VALOR_PAGO,                      -- Valor pago
P.STATUS                           -- Status do pagamento
FROM Pagamento P                   -- Tabela Pagamento
INNER JOIN Pedidos PE              -- Junta com Pedidos
ON P.ID_PEDIDO = PE.ID_PEDIDO      -- Relaciona pagamento ao pedido
INNER JOIN Cliente C               -- Junta com Cliente
ON PE.ID_CLIENTE = C.ID_CLIENTE;   -- Relaciona pedido ao cliente

# Mostra todas as movimentações de entrada e saída dos produtos.
SELECT
PR.NOME,                           -- Nome do produto
M.TIPO,                            -- Tipo da movimentação (Entrada ou Saída)
MP.QUANTIDADE_MOVIMENTADA,         -- Quantidade movimentada
M.DATA_MOVIMENTACAO                -- Data da movimentação
FROM Movimentacao_Produtos MP      -- Tabela intermediária
INNER JOIN Produtos PR             -- Junta com Produtos
ON MP.ID_PRODUTO = PR.ID_PRODUTO   -- Relaciona o produto
INNER JOIN Movimentacao M          -- Junta com Movimentação
ON MP.ID_MOVIMENTACAO = M.ID_MOVIMENTACAO; -- Relaciona a movimentação

# Calcula o valor total do estoque por categoria.
SELECT
C.NOME,                                              -- Nome da categoria
SUM(P.QUANTIDADE_DISPONIVEL * P.VALOR_UNITARIO)
AS VALOR_ESTOQUE                                     -- Soma do valor total do estoque
FROM Produtos P
INNER JOIN Categoria C
ON P.ID_CATEGORIA = C.ID_CATEGORIA
GROUP BY C.NOME;                                     -- Agrupa os resultados por categoria

# Conta quantos produtos existem em cada categoria.
SELECT
C.NOME,                                -- Nome da categoria
COUNT(P.ID_PRODUTO) AS TOTAL_PRODUTOS  -- Conta os produtos
FROM Produtos P
INNER JOIN Categoria C
ON P.ID_CATEGORIA = C.ID_CATEGORIA
GROUP BY C.NOME;                       -- Agrupa por categoria

# Mostra apenas categorias cujo valor em estoque seja superior a R$ 10.000.
SELECT
C.NOME,
SUM(P.QUANTIDADE_DISPONIVEL * P.VALOR_UNITARIO)
AS VALOR_ESTOQUE
FROM Produtos P
INNER JOIN Categoria C
ON P.ID_CATEGORIA = C.ID_CATEGORIA
GROUP BY C.NOME
HAVING VALOR_ESTOQUE > 10000;          -- Filtra os grupos após a soma

# Lista os produtos que possuem preço acima da média.
SELECT
NOME,                                  -- Nome do produto
VALOR_UNITARIO                         -- Valor do produto
FROM Produtos
WHERE VALOR_UNITARIO >                 -- Compara o preço do produto
(
SELECT AVG(VALOR_UNITARIO) FROM Produtos           -- Calcula a média de preço
);

# Atualiza o preço do produto de código 1.
UPDATE Produtos
SET VALOR_UNITARIO = 700.00            -- Novo valor do produto
WHERE ID_PRODUTO = 1;                  -- Produto que será alterado

# Atualiza o status do pedido.
UPDATE Pedidos
SET STATUS = "ENTREGUE"                -- Novo status
WHERE ID_PEDIDO = 3;                   -- Pedido que será atualizado

# Exclui um pagamento.
DELETE FROM Pagamento WHERE ID_PAGAMENTO = 2;                -- Remove o pagamento de código 2

# Ordena os produtos do maior para o menor preço.
SELECT * FROM Produtos ORDER BY VALOR_UNITARIO DESC;          -- Ordenação decrescente

# Conta a quantidade total de produtos cadastrados.
SELECT COUNT(*) AS TOTAL_PRODUTOS FROM Produtos;

# Calcula a média dos preços dos produtos.
SELECT AVG(VALOR_UNITARIO) AS MEDIA_PRECO FROM Produtos;

# Retorna o maior preço cadastrado.
SELECT MAX(VALOR_UNITARIO) AS MAIOR_PRECO FROM Produtos;

# Retorna o menor preço cadastrado.
SELECT MIN(VALOR_UNITARIO) AS MENOR_PRECO FROM Produtos;
