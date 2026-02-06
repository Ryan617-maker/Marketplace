from flask import Flask,render_template

app = Flask(__name__)

@app.route('/')
def Page_Home():
    return render_template("home.html")


@app.route('/Produtos')
def Page_Produtos():
    itens=[
        {'id':1, 'nome':'Celular', 'cod_barra':3032241, 'preco':1200 },
        {'id':1, 'nome':'Celular', 'cod_barra':3032241, 'preco':1200 },
        {'id':1, 'nome':'Celular', 'cod_barra':3032241, 'preco':1200 }
        ]





    return render_template("Produtos.html", itens=itens)