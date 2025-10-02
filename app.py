from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import datetime
import os

# --- ATENÇÃO: Nenhuma pasta 'templates' é necessária! ---

# --- Configuração Inicial do Flask e SQLAlchemy ---
app = Flask(__name__)

# Configura o banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ferramentas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Definição do Modelo do Banco de Dados ---
class Ferramenta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, default=0)
    movimentos = db.relationship('Movimento', backref='ferramenta', lazy=True, cascade="all, delete-orphan")

class Movimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(10), nullable=False) # 'SAIDA' ou 'ENTRADA'
    quantidade = db.Column(db.Integer, default=1, nullable=False)
    data_movimento = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    ferramenta_id = db.Column(db.Integer, db.ForeignKey('ferramenta.id'), nullable=False)

# --- Conteúdo HTML (Agora como strings Python) ---

INDEX_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Controle de Inventário de Ferramentas</title>
    <!-- Carrega Tailwind CSS para estilização moderna e responsiva -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                },
            },
        }
    </script>
</head>
<body class="bg-gray-100 min-h-screen p-4 md:p-8 font-sans">
    <div class="max-w-7xl mx-auto">

        <!-- Mensagem de sucesso após o reset do DB -->
        {% if reset_success == 'true' %}
        <div id="reset-alert" class="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6 rounded-lg shadow-md" role="alert">
            <p class="font-bold">Atenção!</p>
            <p>O banco de dados foi resetado (arquivo 'ferramentas.db' deletado e recriado). Você perdeu todos os dados, mas o erro de coluna foi corrigido. Comece cadastrando novas ferramentas.</p>
        </div>
        {% endif %}
        
        <!-- Cabeçalho Principal -->
        <h1 class="text-4xl sm:text-5xl font-extrabold text-gray-900 mb-4 border-b-4 border-indigo-600 pb-3">
            Inventário de Ferramentas
        </h1>
        
        <!-- Botão de Reset -->
        <a href="{{ url_for('reset_database') }}" 
            class="inline-flex items-center text-sm font-medium text-red-500 hover:text-red-700 transition duration-150 mb-8">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.91 8.91 0 0020 12a9 9 0 10-2.354 5.646L20 20M4 12a8 8 0 1116 0"></path></svg>
            Resetar Banco de Dados (Apaga Todos os Dados!)
        </a>


        <!-- Seção de Cadastro de Nova Ferramenta -->
        <div class="bg-white shadow-xl rounded-xl p-6 mb-10 border border-gray-200">
            <h2 class="text-2xl font-semibold text-indigo-700 mb-4 flex items-center">
                <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                Cadastrar Nova Ferramenta
            </h2>
            <form action="{{ url_for('cadastrar_ferramenta') }}" method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div class="md:col-span-2">
                    <label for="nome" class="block text-sm font-medium text-gray-700">Nome da Ferramenta</label>
                    <input type="text" id="nome" name="nome" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2.5 border focus:ring-indigo-500 focus:border-indigo-500" placeholder="Ex: Chave de Fenda Phillips #2">
                </div>
                <div class="md:col-span-1">
                    <label for="quantidade" class="block text-sm font-medium text-gray-700">Qtd. Inicial</label>
                    <input type="number" id="quantidade" name="quantidade" required min="0" value="0" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2.5 border focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div class="md:col-span-1">
                    <button type="submit" class="w-full bg-indigo-600 text-white py-2.5 px-4 rounded-lg hover:bg-indigo-700 transition duration-150 shadow-md font-medium text-base">
                        Adicionar ao Inventário
                    </button>
                </div>
            </form>
        </div>

        <!-- Seção de Estoque Atual -->
        <h2 class="text-3xl font-bold text-gray-800 mb-6 mt-12">Estoque Atual e Movimentação</h2>
        
        {% if ferramentas %}
            <div class="space-y-6">
            {% for ferramenta in ferramentas %}
                <div class="bg-white shadow-2xl rounded-xl p-6 border-l-8 {% if ferramenta.quantidade > 0 %}border-green-500{% else %}border-red-500{% endif %}">
                    <div class="lg:flex lg:justify-between lg:items-start space-y-4 lg:space-y-0">
                        
                        <!-- Detalhes da Ferramenta -->
                        <div class="lg:w-1/4">
                            <p class="text-xs font-medium text-gray-500 uppercase tracking-wider">ID: {{ ferramenta.id }}</p>
                            <h3 class="text-2xl font-extrabold text-gray-900">{{ ferramenta.nome }}</h3>
                            <p class="text-xl mt-3 font-semibold {% if ferramenta.quantidade > 5 %}text-green-600{% elif ferramenta.quantidade > 0 %}text-yellow-600{% else %}text-red-600{% endif %}">
                                Saldo: <span class="font-black">{{ ferramenta.quantidade }}</span> un.
                            </p>
                            {% if ferramenta.quantidade == 0 %}
                                <span class="inline-block mt-1 px-3 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">ESTOQUE ZERADO</span>
                            {% endif %}
                            
                            <!-- Ações de Gerenciamento -->
                            <div class="flex flex-col space-y-2 mt-4 text-sm font-medium">
                                <a href="{{ url_for('historico', ferramenta_id=ferramenta.id) }}" 
                                    class="inline-flex items-center text-indigo-600 hover:text-indigo-800 transition duration-150">
                                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                    Ver Histórico
                                </a>
                                
                                <a href="{{ url_for('editar_ferramenta', ferramenta_id=ferramenta.id) }}" 
                                    class="inline-flex items-center text-yellow-600 hover:text-yellow-800 transition duration-150">
                                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                                    Editar Item
                                </a>
                                
                                <form action="{{ url_for('deletar_ferramenta', ferramenta_id=ferramenta.id) }}" method="POST" onsubmit="return confirm('ATENÇÃO: Você tem certeza que deseja DELETAR a ferramenta \'{{ ferramenta.nome }}\' e todo o seu histórico de movimentos?')">
                                    <button type="submit" class="inline-flex items-center text-red-600 hover:text-red-800 transition duration-150">
                                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                        Excluir Item
                                    </button>
                                </form>

                            </div>
                            
                        </div>
                        
                        <!-- Formulários de Movimentação (SAÍDA e ENTRADA) -->
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 lg:w-3/4 lg:ml-8">
                            
                            <!-- Form SAIDA (Retirada) -->
                            <form action="{{ url_for('registrar_movimento', ferramenta_id=ferramenta.id, tipo='SAIDA') }}" method="POST" class="bg-red-50 p-4 rounded-lg border border-red-300 shadow-inner">
                                <p class="text-red-700 font-bold mb-3 text-lg">SAÍDA (Retirada)</p>
                                <div class="flex flex-col space-y-3">
                                    <input type="text" name="usuario" placeholder="Nome do Usuário" required class="p-2.5 border border-red-300 rounded-md text-sm focus:ring-red-500 focus:border-red-500">
                                    <input type="number" name="quantidade_movimento" placeholder="Qtd. a Retirar" required min="1" max="{{ ferramenta.quantidade }}" class="p-2.5 border border-red-300 rounded-md text-sm focus:ring-red-500 focus:border-red-500">
                                    <button type="submit" class="w-full bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 transition duration-150 shadow-md font-medium" 
                                            {% if ferramenta.quantidade == 0 %}disabled{% endif %}>
                                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 13l-5 5m0 0l-5-5m5 5V6"></path></svg>
                                        Registrar Retirada
                                    </button>
                                </div>
                                {% if ferramenta.quantidade == 0 %}
                                    <p class="text-xs text-red-500 mt-2 font-medium">Não é possível retirar, saldo atual é zero.</p>
                                {% endif %}
                            </form>
                            
                            <!-- Form ENTRADA (Devolução) -->
                            <form action="{{ url_for('registrar_movimento', ferramenta_id=ferramenta.id, tipo='ENTRADA') }}" method="POST" class="bg-green-50 p-4 rounded-lg border border-green-300 shadow-inner">
                                <p class="text-green-700 font-bold mb-3 text-lg">ENTRADA (Devolução)</p>
                                <div class="flex flex-col space-y-3">
                                    <input type="text" name="usuario" placeholder="Nome do Usuário" required class="p-2.5 border border-green-300 rounded-md text-sm focus:ring-green-500 focus:border-green-500">
                                    <input type="number" name="quantidade_movimento" placeholder="Qtd. a Devolver" required min="1" class="p-2.5 border border-green-300 rounded-md text-sm focus:ring-green-500 focus:border-green-500">
                                    <button type="submit" class="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition duration-150 shadow-md font-medium">
                                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11l5-5m0 0l5 5m-5-5v12"></path></svg>
                                        Registrar Devolução
                                    </button>
                                </div>
                            </form>

                        </div>
                    </div>
                </div>
            {% endfor %}
            </div>
        {% else %}
            <!-- Mensagem se não houver ferramentas -->
            <div class="text-center p-12 bg-white rounded-xl shadow-lg border-2 border-dashed border-gray-300">
                <p class="text-xl text-gray-500 font-medium">Nenhuma ferramenta cadastrada ainda.</p>
                <p class="text-base text-gray-400 mt-2">Use o formulário acima para adicionar o primeiro item ao seu inventário.</p>
            </div>
        {% endif %}
        
        <div class="h-16"></div> 

    </div>
</body>
</html>
"""

HISTORICO_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Histórico de {{ ferramenta.nome }}</title>
    <!-- Carrega Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                },
            },
        }
    </script>
</head>
<body class="bg-gray-100 min-h-screen p-4 md:p-8 font-sans">
    <div class="max-w-4xl mx-auto">
        
        <!-- Link de Retorno -->
        <a href="{{ url_for('index') }}" class="inline-flex items-center text-indigo-600 hover:text-indigo-800 transition duration-150 mb-6 font-medium">
            <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
            Voltar para o Inventário
        </a>

        <!-- Cabeçalho de Histórico -->
        <div class="bg-white shadow-xl rounded-xl p-6 mb-8 border-t-4 border-indigo-500">
            <h1 class="text-3xl font-extrabold text-gray-900 mb-2">
                Histórico de Movimentos
            </h1>
            <h2 class="text-2xl font-semibold text-indigo-700">
                {{ ferramenta.nome }} (ID: {{ ferramenta.id }})
            </h2>
            <p class="text-xl mt-3 font-bold text-gray-600">
                Saldo Atual: 
                <span class="font-black {% if ferramenta.quantidade > 5 %}text-green-600{% elif ferramenta.quantidade > 0 %}text-yellow-600{% else %}text-red-600{% endif %}">
                    {{ ferramenta.quantidade }} un.
                </span>
            </p>
        </div>

        <!-- Lista de Movimentos -->
        {% if movimentos %}
            <div class="space-y-4">
                {% for movimento in movimentos %}
                    {% set is_saida = movimento.tipo == 'SAIDA' %}
                    <div class="p-4 rounded-lg shadow-md border-l-4 
                                {% if is_saida %}bg-red-50 border-red-500{% else %}bg-green-50 border-green-500{% endif %}">
                        
                        <div class="flex justify-between items-center">
                            <!-- Tipo e Quantidade -->
                            <div>
                                <span class="text-lg font-bold uppercase 
                                              {% if is_saida %}text-red-700{% else %}text-green-700{% endif %}">
                                    {{ movimento.tipo }}
                                </span>
                                <span class="text-xl font-extrabold ml-3">
                                    {{ movimento.quantidade }} unidades
                                </span>
                            </div>

                            <!-- Data -->
                            <p class="text-sm text-gray-500">
                                {{ movimento.data_movimento.strftime('%d/%m/%Y %H:%M:%S') }}
                            </p>
                        </div>

                        <!-- Usuário -->
                        <p class="mt-2 text-base text-gray-800">
                            Usuário: <span class="font-semibold">{{ movimento.usuario }}</span>
                        </p>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <!-- Mensagem se não houver movimentos -->
            <div class="text-center p-8 bg-white rounded-xl shadow-lg border-2 border-dashed border-gray-300 mt-8">
                <p class="text-lg text-gray-500 font-medium">Esta ferramenta ainda não possui registros de entrada ou saída.</p>
            </div>
        {% endif %}
        
        <div class="h-16"></div> 

    </div>
</body>
</html>
"""

EDITAR_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar {{ ferramenta.nome }}</title>
    <!-- Carrega Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                },
            },
        }
    </script>
</head>
<body class="bg-gray-100 min-h-screen p-4 md:p-8 font-sans">
    <div class="max-w-xl mx-auto">
        
        <!-- Link de Retorno -->
        <a href="{{ url_for('index') }}" class="inline-flex items-center text-indigo-600 hover:text-indigo-800 transition duration-150 mb-6 font-medium">
            <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
            Cancelar e Voltar
        </a>

        <!-- Cartão de Edição -->
        <div class="bg-white shadow-2xl rounded-xl p-8 border-t-4 border-yellow-500">
            <h1 class="text-3xl font-extrabold text-gray-900 mb-2">
                Editando Ferramenta
            </h1>
            <h2 class="text-xl font-semibold text-yellow-700 mb-6">
                {{ ferramenta.nome }} (ID: {{ ferramenta.id }})
            </h2>

            <form action="{{ url_for('editar_ferramenta', ferramenta_id=ferramenta.id) }}" method="POST" class="space-y-6">
                
                <!-- Campo Nome -->
                <div>
                    <label for="nome" class="block text-sm font-medium text-gray-700">Novo Nome da Ferramenta</label>
                    <input type="text" id="nome" name="nome" required 
                            value="{{ ferramenta.nome }}"
                            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-3 border focus:ring-yellow-500 focus:border-yellow-500" 
                            placeholder="Ex: Chave de Fenda Phillips #2">
                </div>
                
                <!-- Campo Quantidade Atual -->
                <div>
                    <label for="quantidade" class="block text-sm font-medium text-gray-700">Quantidade Atual em Estoque</label>
                    <input type="number" id="quantidade" name="quantidade" required min="0" 
                            value="{{ ferramenta.quantidade }}"
                            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-3 border focus:ring-yellow-500 focus:border-yellow-500">
                    <p class="mt-2 text-sm text-gray-500">
                        Ajuste este valor se precisar corrigir o saldo atual. Para registrar retiradas ou devoluções normais, use a página principal.
                    </p>
                </div>
                
                <!-- Botão Salvar -->
                <button type="submit" class="w-full bg-yellow-600 text-white py-3 px-4 rounded-lg hover:bg-yellow-700 transition duration-150 shadow-md font-bold text-base">
                    <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.618a8.955 8.955 0 011.67 3.659A9 9 0 0112 21a9 9 0 01-5.288-1.618A8.955 8.955 0 014 12c0-1.688.452-3.298 1.258-4.707L16.404 4.596z"></path></svg>
                    Salvar Alterações
                </button>
            </form>
        </div>
        
        <div class="h-16"></div>

    </div>
</body>
</html>
"""


# --- Rotas da Aplicação Web (Usando render_template_string) ---

@app.route('/')
def index():
    """Rota principal: Exibe o dashboard com todas as ferramentas e saldos."""
    todas_ferramentas = Ferramenta.query.all()
    # Adiciona a verificação do parâmetro de reset_success
    reset_success = request.args.get('reset_success')
    return render_template_string(INDEX_HTML, ferramentas=todas_ferramentas, reset_success=reset_success)

@app.route('/cadastrar', methods=['POST'])
def cadastrar_ferramenta():
    """Processa o formulário de cadastro de nova ferramenta."""
    nome = request.form.get('nome').strip()
    
    try:
        quantidade = int(request.form.get('quantidade'))
    except ValueError:
        return redirect(url_for('index'))

    if nome and quantidade >= 0:
        nova_ferramenta = Ferramenta(nome=nome, quantidade=quantidade)
        db.session.add(nova_ferramenta)
        db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/movimento/<int:ferramenta_id>/<string:tipo>', methods=['POST'])
def registrar_movimento(ferramenta_id, tipo):
    """Processa a retirada (SAIDA) ou devolução (ENTRADA) de uma ferramenta."""
    ferramenta = Ferramenta.query.get_or_404(ferramenta_id)
    usuario = request.form.get('usuario').strip()
    
    try:
        quantidade_movimento = int(request.form.get('quantidade_movimento'))
    except:
        return redirect(url_for('index'))

    if not usuario or quantidade_movimento <= 0:
        return redirect(url_for('index'))

    if tipo == 'SAIDA':
        if ferramenta.quantidade >= quantidade_movimento:
            ferramenta.quantidade -= quantidade_movimento
            movimento = Movimento(usuario=usuario, 
                                  tipo='SAIDA', 
                                  quantidade=quantidade_movimento,
                                  ferramenta_id=ferramenta_id)
            db.session.add(movimento)
            db.session.commit()
            
    elif tipo == 'ENTRADA':
        ferramenta.quantidade += quantidade_movimento
        movimento = Movimento(usuario=usuario, 
                              tipo='ENTRADA', 
                              quantidade=quantidade_movimento,
                              ferramenta_id=ferramenta_id)
        db.session.add(movimento)
        db.session.commit()

    return redirect(url_for('index'))

@app.route('/historico/<int:ferramenta_id>')
def historico(ferramenta_id):
    """Rota para exibir o histórico de movimentos de uma ferramenta específica."""
    ferramenta = Ferramenta.query.get_or_404(ferramenta_id)
    movimentos = Movimento.query.filter_by(ferramenta_id=ferramenta_id).order_by(Movimento.data_movimento.desc()).all()
    
    # Renderiza a string HTML do histórico
    return render_template_string(HISTORICO_HTML, ferramenta=ferramenta, movimentos=movimentos)


@app.route('/editar/<int:ferramenta_id>', methods=['GET', 'POST'])
def editar_ferramenta(ferramenta_id):
    """Exibe o formulário de edição (GET) ou processa a atualização (POST)."""
    ferramenta = Ferramenta.query.get_or_404(ferramenta_id)

    if request.method == 'POST':
        novo_nome = request.form.get('nome').strip()
        
        try:
            nova_quantidade = int(request.form.get('quantidade'))
        except ValueError:
            return redirect(url_for('index'))
            
        if novo_nome:
            ferramenta.nome = novo_nome
            ferramenta.quantidade = nova_quantidade
            db.session.commit()
        return redirect(url_for('index'))
        
    # Renderiza a string HTML de edição
    return render_template_string(EDITAR_HTML, ferramenta=ferramenta)

@app.route('/deletar/<int:ferramenta_id>', methods=['POST'])
def deletar_ferramenta(ferramenta_id):
    """Deleta uma ferramenta e seus movimentos relacionados."""
    ferramenta = Ferramenta.query.get_or_404(ferramenta_id)
    
    db.session.delete(ferramenta)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/reset-db')
def reset_database():
    """Rota para deletar e recriar o banco de dados, resolvendo o erro de coluna."""
    db_path = 'ferramentas.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Recria as tabelas (agora com a coluna 'quantidade')
    with app.app_context():
        db.create_all()
        
    # Redireciona para a página inicial com um parâmetro de sucesso
    return redirect(url_for('index', reset_success='true'))

# --- Inicialização ---
with app.app_context():
    # Cria as tabelas (ou as recria se o arquivo ferramentas.db for deletado)
    db.create_all()

if __name__ == '__main__':
    # Mudança de debug=True para debug=False em ambiente de produção
    print("Sistema de Controle de Ferramentas rodando em: http://127.0.0.1:5000 (Local)")
    # Uso de porta dinâmica para serviços de hospedagem como Heroku ou Render
    port = int(os.environ.get('PORT', 5000))
    # Quando em produção, o servidor Gunicorn é geralmente usado para servir o app,
    # então esta parte é mais para rodar localmente.
    app.run(debug=False, host='0.0.0.0', port=port)
