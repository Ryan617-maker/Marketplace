from flask import Flask, render_template, request, redirect, url_for, flash, session
from conexao import conectar
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'marketplace_secreta_key_2026'



# ============================================================
# PÁGINA INICIAL
# ============================================================
@app.route('/')
def index():
    # Se já estiver logado como administrador
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))

    # Se já estiver logado como cliente
    if 'cliente_id' in session:
        return redirect(url_for('cliente_dashboard'))

    # Caso contrário, vai para a tela de login
    return redirect(url_for('login'))


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def formatar_moeda(valor):
    return "R$ {:,.2f}".format(valor).replace(',', '_').replace('.', ',').replace('_', '.')


def formatar_data(data):
    if data is None:
        return ''
    return data.strftime('%d/%m/%Y') if hasattr(data, 'strftime') else str(data)[:10].split('-')[::-1][::-1]


def formatar_data_pt(data):
    """Formata data de YYYY-MM-DD para DD/MM/YYYY"""
    if data is None:
        return ''
    s = str(data)[:10]
    parts = s.split('-')
    if len(parts) == 3:
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return s


def login_required_admin(f):
    """Decorator para exigir login de admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Acesso negado. Faça login como administrador.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def login_required_cliente(f):
    """Decorator para exigir login de cliente"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'cliente_id' not in session:
            flash('Acesso negado. Faça login.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# LOGIN / LOGOUT
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se já está logado como admin, redireciona
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    # Se já está logado como cliente, redireciona
    if 'cliente_id' in session:
        return redirect(url_for('cliente_dashboard'))

    if request.method == 'POST':
        cpf = request.form['cpf']
        senha = request.form['senha']
        tipo = request.form.get('tipo', 'admin')

        conn = conectar()
        cursor = conn.cursor(dictionary=True)

        if tipo == 'admin':
            # Admin: CPF = admin e senha fixa
            if cpf == 'admin' and senha == 'admin123':
                session['admin_logged_in'] = True
                session['tipo_usuario'] = 'admin'
                flash('Bem-vindo, Administrador!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('CPF ou senha inválidos para Administrador.', 'danger')
        elif tipo == 'cliente':
            # Cliente: Login por CPF e senha cadastrada
            cursor.execute("SELECT * FROM Cliente WHERE CPF = %s", (cpf,))
            cliente = cursor.fetchone()

            if cliente and check_password_hash(cliente.get('SENHA', ''), senha):
                session['cliente_id'] = cliente['ID_CLIENTE']
                session['cliente_nome'] = cliente['NOME']
                session['cliente_cpf'] = cliente['CPF']
                session['tipo_usuario'] = 'cliente'
                flash(f'Bem-vindo, {cliente["NOME"]}!', 'success')
                return redirect(url_for('cliente_dashboard'))
            else:
                flash('CPF ou senha inválidos para Cliente.', 'danger')

        cursor.close()
        conn.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu com sucesso!', 'info')
    return redirect(url_for('login'))


# ============================================================
# ÁREA ADMIN
# ============================================================
@app.route('/admin')
@login_required_admin
def admin_dashboard():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM Produtos")
    total_produtos = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS total FROM Cliente")
    total_clientes = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS total FROM Pedidos")
    total_pedidos = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS total FROM Pagamento")
    total_pagamentos = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS total FROM Estoque")
    total_estoque = cursor.fetchone()['total']

    # Últimos pedidos
    cursor.execute("""
        SELECT PE.ID_PEDIDO, C.NOME AS CLIENTE, PE.DATA_PEDIDO, 
               PE.VALOR_TOTAL, PE.STATUS
        FROM Pedidos PE
        INNER JOIN Cliente C ON PE.ID_CLIENTE = C.ID_CLIENTE
        ORDER BY PE.DATA_PEDIDO DESC LIMIT 5
    """)
    ultimos_pedidos = cursor.fetchall()

    # Alertas de estoque baixo
    cursor.execute("""
        SELECT E.ID_ESTOQUE, P.NOME AS PRODUTO, E.QUANTIDADE_ESTOQUE, E.LIMITE_MINIMO
        FROM Estoque E
        INNER JOIN Produtos P ON E.ID_PRODUTO = P.ID_PRODUTO
        WHERE E.QUANTIDADE_ESTOQUE <= E.LIMITE_MINIMO
        ORDER BY E.QUANTIDADE_ESTOQUE
    """)
    alertas_estoque = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin/dashboard.html',
                           total_produtos=total_produtos,
                           total_clientes=total_clientes,
                           total_pedidos=total_pedidos,
                           total_pagamentos=total_pagamentos,
                           total_estoque=total_estoque,
                           ultimos_pedidos=ultimos_pedidos,
                           alertas_estoque=alertas_estoque)


# ============================================================
# ADMIN - PRODUTOS
# ============================================================
@app.route('/admin/produtos')
@login_required_admin
def admin_produtos():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT P.ID_PRODUTO, P.NOME, P.QUANTIDADE_DISPONIVEL, 
               P.VALOR_UNITARIO, C.NOME AS CATEGORIA
        FROM Produtos P
        INNER JOIN Categoria C ON P.ID_CATEGORIA = C.ID_CATEGORIA
        ORDER BY P.ID_PRODUTO
    """)
    produtos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/produtos.html', produtos=produtos)


@app.route('/admin/produto/adicionar', methods=['GET', 'POST'])
@login_required_admin
def admin_adicionar_produto():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nome = request.form['nome']
        quantidade = request.form['quantidade_disponivel']
        valor = request.form['valor_unitario']
        categoria = request.form['id_categoria']

        cursor.execute(
            "INSERT INTO Produtos (NOME, QUANTIDADE_DISPONIVEL, VALOR_UNITARIO, ID_CATEGORIA) VALUES (%s, %s, %s, %s)",
            (nome, int(quantidade), float(valor), int(categoria))
        )
        conn.commit()

        cursor.execute(
            "INSERT INTO Estoque (QUANTIDADE_ESTOQUE, LIMITE_MAXIMO, LIMITE_MINIMO, ID_PRODUTO) VALUES (%s, %s, %s, %s)",
            (int(quantidade), int(quantidade) * 5, int(quantidade) // 3, cursor.lastrowid)
        )
        conn.commit()

        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('admin_produtos'))

    cursor.execute("SELECT * FROM Categoria ORDER BY NOME")
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/formulario_produto.html', categorias=categorias, produto=None)


@app.route('/admin/produto/editar/<int:id>', methods=['GET', 'POST'])
@login_required_admin
def admin_editar_produto(id):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nome = request.form['nome']
        quantidade = request.form['quantidade_disponivel']
        valor = request.form['valor_unitario']
        categoria = request.form['id_categoria']

        cursor.execute(
            "UPDATE Produtos SET NOME=%s, QUANTIDADE_DISPONIVEL=%s, VALOR_UNITARIO=%s, ID_CATEGORIA=%s WHERE ID_PRODUTO=%s",
            (nome, int(quantidade), float(valor), int(categoria), id)
        )
        conn.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin_produtos'))

    cursor.execute("""
        SELECT P.*, C.NOME AS CATEGORIA FROM Produtos P
        INNER JOIN Categoria C ON P.ID_CATEGORIA = C.ID_CATEGORIA
        WHERE P.ID_PRODUTO = %s
    """, (id,))
    produto = cursor.fetchone()

    cursor.execute("SELECT * FROM Categoria ORDER BY NOME")
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/formulario_produto.html', produto=produto, categorias=categorias)


@app.route('/admin/produto/excluir/<int:id>')
@login_required_admin
def admin_excluir_produto(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Estoque WHERE ID_PRODUTO = %s", (id,))
    cursor.execute("DELETE FROM Produtos WHERE ID_PRODUTO = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('admin_produtos'))


# ============================================================
# ADMIN - CLIENTES
# ============================================================
@app.route('/admin/clientes')
@login_required_admin
def admin_clientes():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ID_CLIENTE, NOME, CPF, DATA_NASCIMENTO, SEXO FROM Cliente ORDER BY ID_CLIENTE")
    clientes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/clientes.html', clientes=clientes)


@app.route('/admin/cliente/adicionar', methods=['GET', 'POST'])
@login_required_admin
def admin_adicionar_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        data_nasc = request.form['data_nascimento']
        sexo = request.form['sexo']
        senha = request.form['senha']

        conn = conectar()
        cursor = conn.cursor()
        senha_hash = generate_password_hash(senha)
        cursor.execute(
            "INSERT INTO Cliente (NOME, CPF, DATA_NASCIMENTO, SEXO, SENHA) VALUES (%s, %s, %s, %s, %s)",
            (nome, cpf, data_nasc, sexo, senha_hash)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash('Cliente adicionado com sucesso!', 'success')
        return redirect(url_for('admin_clientes'))

    return render_template('admin/formulario_cliente.html', cliente=None)


@app.route('/admin/cliente/editar/<int:id>', methods=['GET', 'POST'])
@login_required_admin
def admin_editar_cliente(id):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        data_nasc = request.form['data_nascimento']
        sexo = request.form['sexo']
        nova_senha = request.form.get('senha', '')

        if nova_senha:
            senha_hash = generate_password_hash(nova_senha)
            cursor.execute(
                "UPDATE Cliente SET NOME=%s, CPF=%s, DATA_NASCIMENTO=%s, SEXO=%s, SENHA=%s WHERE ID_CLIENTE=%s",
                (nome, cpf, data_nasc, sexo, senha_hash, id)
            )
        else:
            cursor.execute(
                "UPDATE Cliente SET NOME=%s, CPF=%s, DATA_NASCIMENTO=%s, SEXO=%s WHERE ID_CLIENTE=%s",
                (nome, cpf, data_nasc, sexo, id)
            )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('admin_clientes'))

    cursor.execute("SELECT * FROM Cliente WHERE ID_CLIENTE = %s", (id,))
    cliente = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('admin/formulario_cliente.html', cliente=cliente)


@app.route('/admin/cliente/excluir/<int:id>')
@login_required_admin
def admin_excluir_cliente(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Cliente WHERE ID_CLIENTE = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('admin_clientes'))


# ============================================================
# ADMIN - PEDIDOS
# ============================================================
@app.route('/admin/pedidos')
@login_required_admin
def admin_pedidos():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT PE.ID_PEDIDO, C.NOME AS CLIENTE, PE.DATA_PEDIDO, 
               PE.VALOR_TOTAL, PE.STATUS
        FROM Pedidos PE
        INNER JOIN Cliente C ON PE.ID_CLIENTE = C.ID_CLIENTE
        ORDER BY PE.ID_PEDIDO
    """)
    pedidos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/pedidos.html', pedidos=pedidos)


@app.route('/admin/pedido/adicionar', methods=['GET', 'POST'])
@login_required_admin
def admin_adicionar_pedido():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        data_pedido = request.form['data_pedido']
        valor_total = request.form['valor_total']
        status = request.form['status']
        id_cliente = request.form['id_cliente']

        cursor.execute(
            "INSERT INTO Pedidos (DATA_PEDIDO, VALOR_TOTAL, STATUS, ID_CLIENTE) VALUES (%s, %s, %s, %s)",
            (data_pedido, float(valor_total), status, int(id_cliente))
        )
        conn.commit()
        flash('Pedido adicionado com sucesso!', 'success')
        return redirect(url_for('admin_pedidos'))

    cursor.execute("SELECT * FROM Cliente ORDER BY NOME")
    clientes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/formulario_pedido.html', pedido=None, clientes=clientes)


@app.route('/admin/pedido/editar/<int:id>', methods=['GET', 'POST'])
@login_required_admin
def admin_editar_pedido(id):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        data_pedido = request.form['data_pedido']
        valor_total = request.form['valor_total']
        status = request.form['status']
        id_cliente = request.form['id_cliente']

        cursor.execute(
            "UPDATE Pedidos SET DATA_PEDIDO=%s, VALOR_TOTAL=%s, STATUS=%s, ID_CLIENTE=%s WHERE ID_PEDIDO=%s",
            (data_pedido, float(valor_total), status, int(id_cliente), id)
        )
        conn.commit()
        flash('Pedido atualizado com sucesso!', 'success')
        return redirect(url_for('admin_pedidos'))

    cursor.execute("SELECT * FROM Pedidos WHERE ID_PEDIDO = %s", (id,))
    pedido = cursor.fetchone()
    cursor.execute("SELECT * FROM Cliente ORDER BY NOME")
    clientes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/formulario_pedido.html', pedido=pedido, clientes=clientes)


@app.route('/admin/pedido/excluir/<int:id>')
@login_required_admin
def admin_excluir_pedido(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Pagamento WHERE ID_PEDIDO = %s", (id,))
    cursor.execute("DELETE FROM Pedidos WHERE ID_PEDIDO = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Pedido excluído com sucesso!', 'success')
    return redirect(url_for('admin_pedidos'))


# ============================================================
# ADMIN - PAGAMENTOS
# ============================================================
@app.route('/admin/pagamentos')
@login_required_admin
def admin_pagamentos():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT PA.ID_PAGAMENTO, C.NOME AS CLIENTE, 
               PA.FORMA_PAGAMENTO, PA.VALOR_PAGO, 
               PA.DATA_PAGAMENTO, PA.STATUS, PA.ID_PEDIDO
        FROM Pagamento PA
        INNER JOIN Pedidos PE ON PA.ID_PEDIDO = PE.ID_PEDIDO
        INNER JOIN Cliente C ON PE.ID_CLIENTE = C.ID_CLIENTE
        ORDER BY PA.ID_PAGAMENTO
    """)
    pagamentos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/pagamentos.html', pagamentos=pagamentos)


@app.route('/admin/pagamento/adicionar', methods=['GET', 'POST'])
@login_required_admin
def admin_adicionar_pagamento():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        forma = request.form['forma_pagamento']
        valor = request.form['valor_pago']
        data_pag = request.form['data_pagamento']
        status = request.form['status']
        id_pedido = request.form['id_pedido']

        cursor.execute(
            "INSERT INTO Pagamento (FORMA_PAGAMENTO, VALOR_PAGO, DATA_PAGAMENTO, STATUS, ID_PEDIDO) VALUES (%s, %s, %s, %s, %s)",
            (forma, float(valor), data_pag, status, int(id_pedido))
        )
        conn.commit()
        flash('Pagamento adicionado com sucesso!', 'success')
        return redirect(url_for('admin_pagamentos'))

    cursor.execute("SELECT ID_PEDIDO, DATA_PEDIDO, VALOR_TOTAL FROM Pedidos ORDER BY ID_PEDIDO")
    pedidos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/formulario_pagamento.html', pagamento=None, pedidos=pedidos)


@app.route('/admin/pagamento/editar/<int:id>', methods=['GET', 'POST'])
@login_required_admin
def admin_editar_pagamento(id):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        forma = request.form['forma_pagamento']
        valor = request.form['valor_pago']
        data_pag = request.form['data_pagamento']
        status = request.form['status']
        id_pedido = request.form['id_pedido']

        cursor.execute(
            "UPDATE Pagamento SET FORMA_PAGAMENTO=%s, VALOR_PAGO=%s, DATA_PAGAMENTO=%s, STATUS=%s, ID_PEDIDO=%s WHERE ID_PAGAMENTO=%s",
            (forma, float(valor), data_pag, status, int(id_pedido), id)
        )
        conn.commit()
        flash('Pagamento atualizado com sucesso!', 'success')
        return redirect(url_for('admin_pagamentos'))

    cursor.execute("SELECT * FROM Pagamento WHERE ID_PAGAMENTO = %s", (id,))
    pagamento = cursor.fetchone()
    cursor.execute("SELECT ID_PEDIDO, DATA_PEDIDO, VALOR_TOTAL FROM Pedidos ORDER BY ID_PEDIDO")
    pedidos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/formulario_pagamento.html', pagamento=pagamento, pedidos=pedidos)


@app.route('/admin/pagamento/excluir/<int:id>')
@login_required_admin
def admin_excluir_pagamento(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Pagamento WHERE ID_PAGAMENTO = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Pagamento excluído com sucesso!', 'success')
    return redirect(url_for('admin_pagamentos'))


# ============================================================
# ADMIN - ESTOQUE
# ============================================================
@app.route('/admin/estoque')
@login_required_admin
def admin_estoque():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT E.ID_ESTOQUE, P.NOME AS PRODUTO, C.NOME AS CATEGORIA,
               E.QUANTIDADE_ESTOQUE, E.LIMITE_MAXIMO, E.LIMITE_MINIMO,
               P.VALOR_UNITARIO, P.QUANTIDADE_DISPONIVEL
        FROM Estoque E
        INNER JOIN Produtos P ON E.ID_PRODUTO = P.ID_PRODUTO
        INNER JOIN Categoria C ON P.ID_CATEGORIA = C.ID_CATEGORIA
        ORDER BY E.ID_ESTOQUE
    """)
    estoque = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/estoque.html', estoque=estoque)


@app.route('/admin/estoque/editar/<int:id>', methods=['GET', 'POST'])
@login_required_admin
def admin_editar_estoque(id):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        quantidade = request.form['quantidade_estoque']
        limite_max = request.form['limite_maximo']
        limite_min = request.form['limite_minimo']

        cursor.execute(
            "UPDATE Estoque SET QUANTIDADE_ESTOQUE=%s, LIMITE_MAXIMO=%s, LIMITE_MINIMO=%s WHERE ID_ESTOQUE=%s",
            (int(quantidade), int(limite_max), int(limite_min), id)
        )
        conn.commit()
        flash('Estoque atualizado com sucesso!', 'success')
        return redirect(url_for('admin_estoque'))

    cursor.execute("""
        SELECT E.*, P.NOME AS PRODUTO FROM Estoque E
        INNER JOIN Produtos P ON E.ID_PRODUTO = P.ID_PRODUTO
        WHERE E.ID_ESTOQUE = %s
    """, (id,))
    registro = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('admin/formulario_estoque.html', registro=registro)


# ============================================================
# ADMIN - MOVIMENTAÇÕES
# ============================================================
@app.route('/admin/movimentacoes')
@login_required_admin
def admin_movimentacoes():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT MP.ID_MOVIMENTACAO_PRODUTO, PR.NOME AS PRODUTO,
               M.TIPO, MP.QUANTIDADE_MOVIMENTADA,
               M.DATA_MOVIMENTACAO
        FROM Movimentacao_Produtos MP
        INNER JOIN Produtos PR ON MP.ID_PRODUTO = PR.ID_PRODUTO
        INNER JOIN Movimentacao M ON MP.ID_MOVIMENTACAO = M.ID_MOVIMENTACAO
        ORDER BY M.DATA_MOVIMENTACAO DESC
    """)
    movimentacoes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/movimentacoes.html', movimentacoes=movimentacoes)


# ============================================================
# ÁREA CLIENTE
# ============================================================
@app.route('/cliente')
@login_required_cliente
def cliente_dashboard():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    # Dados do cliente
    cursor.execute("SELECT * FROM Cliente WHERE ID_CLIENTE = %s", (session['cliente_id'],))
    cliente = cursor.fetchone()

    # Pedidos do cliente
    cursor.execute("""
        SELECT PE.ID_PEDIDO, PE.DATA_PEDIDO, PE.VALOR_TOTAL, PE.STATUS
        FROM Pedidos PE
        WHERE PE.ID_CLIENTE = %s
        ORDER BY PE.DATA_PEDIDO DESC
    """, (session['cliente_id'],))
    pedidos = cursor.fetchall()

    # Pagamentos do cliente
    cursor.execute("""
        SELECT PA.ID_PAGAMENTO, PA.FORMA_PAGAMENTO, PA.VALOR_PAGO, 
               PA.DATA_PAGAMENTO, PA.STATUS, PA.ID_PEDIDO
        FROM Pagamento PA
        INNER JOIN Pedidos PE ON PA.ID_PEDIDO = PE.ID_PEDIDO
        WHERE PE.ID_CLIENTE = %s
        ORDER BY PA.DATA_PAGAMENTO DESC
    """, (session['cliente_id'],))
    pagamentos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('cliente/dashboard.html', cliente=cliente, pedidos=pedidos, pagamentos=pagamentos)


@app.route('/cliente/dados', methods=['GET', 'POST'])
@login_required_cliente
def cliente_dados():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nome = request.form['nome']
        data_nasc = request.form['data_nascimento']
        sexo = request.form['sexo']
        nova_senha = request.form.get('senha', '')

        if nova_senha:
            senha_hash = generate_password_hash(nova_senha)
            cursor.execute(
                "UPDATE Cliente SET NOME=%s, DATA_NASCIMENTO=%s, SEXO=%s, SENHA=%s WHERE ID_CLIENTE=%s",
                (nome, data_nasc, sexo, senha_hash, session['cliente_id'])
            )
        else:
            cursor.execute(
                "UPDATE Cliente SET NOME=%s, DATA_NASCIMENTO=%s, SEXO=%s WHERE ID_CLIENTE=%s",
                (nome, data_nasc, sexo, session['cliente_id'])
            )
        conn.commit()
        session['cliente_nome'] = nome
        flash('Dados atualizados com sucesso!', 'success')

    cursor.execute("SELECT * FROM Cliente WHERE ID_CLIENTE = %s", (session['cliente_id'],))
    cliente = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('cliente/dados.html', cliente=cliente)


@app.route('/cliente/pedidos')
@login_required_cliente
def cliente_pedidos():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT PE.ID_PEDIDO, PE.DATA_PEDIDO, PE.VALOR_TOTAL, PE.STATUS
        FROM Pedidos PE
        WHERE PE.ID_CLIENTE = %s
        ORDER BY PE.DATA_PEDIDO DESC
    """, (session['cliente_id'],))
    pedidos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('cliente/pedidos.html', pedidos=pedidos)

@app.route('/cliente/pedido/novo', methods=['GET', 'POST'])
@login_required_cliente
def cliente_novo_pedido():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        data_pedido = request.form['data_pedido']
        valor_total = request.form['valor_total']
        status = request.form['status']

        cursor.execute("""
            INSERT INTO Pedidos (DATA_PEDIDO, VALOR_TOTAL, STATUS, ID_CLIENTE)
            VALUES (%s, %s, %s, %s)
        """, (
            data_pedido,
            float(valor_total),
            status,
            session['cliente_id']
        ))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Pedido realizado com sucesso!', 'success')
        return redirect(url_for('cliente_pedidos'))

    cursor.close()
    conn.close()
    return render_template('cliente/formulario_pedido.html')


@app.route('/cliente/pagamentos')
@login_required_cliente
def cliente_pagamentos():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT PA.ID_PAGAMENTO, PA.FORMA_PAGAMENTO, PA.VALOR_PAGO, 
               PA.DATA_PAGAMENTO, PA.STATUS, PA.ID_PEDIDO
        FROM Pagamento PA
        INNER JOIN Pedidos PE ON PA.ID_PEDIDO = PE.ID_PEDIDO
        WHERE PE.ID_CLIENTE = %s
        ORDER BY PA.DATA_PAGAMENTO DESC
    """, (session['cliente_id'],))
    pagamentos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('cliente/pagamentos.html', pagamentos=pagamentos)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
