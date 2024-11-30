from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = 'tasks_with_errors.db'

# Conexão com banco de dados (possível erro ao não fechar a conexão corretamente)
def connect_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Página principal (Filtro e ordenação com problemas)
@app.route('/')
def index():
    search_query = request.args.get('search', '')  # Busca não remove espaços extras
    sort_by = request.args.get('sort_by', 'priority')  # Ordenação pode não funcionar corretamente

    conn = connect_db()
    cursor = conn.cursor()

    # A lógica do filtro não cobre todos os casos
    query = f"SELECT * FROM tasks WHERE title LIKE ? OR description LIKE ? ORDER BY {sort_by}"
    try:
        cursor.execute(query, (f"%{search_query}%", f"%{search_query}%"))
        tasks = cursor.fetchall()
    except sqlite3.OperationalError:  # Erro ao ordenar por coluna inválida
        tasks = []
    conn.close()

    return render_template('index.html', tasks=tasks, search_query=search_query)

# Adicionar tarefa (Problema: Campos obrigatórios não são validados corretamente)
@app.route('/add', methods=['POST'])
def add_task():
    title = request.form.get('title', '')  # Não verifica se o título é válido
    if len(title) < 3:  # Erro na validação do título (mínimo 3 caracteres)
        return redirect('/')  # Redireciona sem aviso ao usuário

    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO tasks (title, description, category, priority, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, 'Descrição Padrão', 'Trabalho', 'Média', 'Pendente', created_at))
        conn.commit()
    except sqlite3.IntegrityError:  # Problema não tratado de forma amigável
        pass
    conn.close()
    return redirect('/')

# Alternar status (Erro na alternância de status)
@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_status(task_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()

    if not task:  # Se a tarefa não existir, o sistema falha silenciosamente
        conn.close()
        return redirect('/')

    new_status = 'Concluído' if task['status'] == 'Pendente' else 'Invalido'  # Status incorreto
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()
    return redirect('/')

# Excluir tarefa (Sem problemas para referência)
@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect('/')

# Inicializar banco de dados
if __name__ == '__main__':
    conn = connect_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        priority TEXT,
        status TEXT,
        created_at DATETIME
    )
    """)
    conn.close()
    app.run(debug=True)
