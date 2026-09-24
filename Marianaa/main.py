import os

from flask import Flask, render_template, request, flash, redirect, url_for,session
import fdb
from flask_bcrypt import Bcrypt

app = Flask(__name__)

bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'Aqui_é_a_chave_da_turma_a '


host = "localhost"
database = r"C:\Users\Aluno\Downloads\BANCO.FDB"
user = 'sysdba'
password = 'sysdba'

con = fdb.connect(host=host, database=database, user=user, password=password)


@app.route("/")
def index():
    cursor = con.cursor()  # abrindo o cursor
    cursor.execute("""select l.id_livro, l.nome, l.autor, l.ano_publicacao
                      from livro l
                      order by l.nome""")

    livros = cursor.fetchall()

    cursor.close()

    return render_template('index.html', livros=livros)


@app.route("/novo")
def novo():
    if 'id_usuario' not in session:
        flash('Precisa estar logado')
        return redirect(url_for("login"))
    return render_template('novo.html',titulo="Novo Livro")

@app.route("/criar", methods=['POST'])
def criar():

    nome = request.form['nome']
    autor = request.form['autor']
    ano_publicado = request.form['ano_publicacao']

    cursor = con.cursor()

    try:

        cursor.execute("""SELECT 1 FROM livro WHERE nome = ?""", (nome,))

        if cursor.fetchone():
            flash("Erro Livro já cadastrado!")
            return redirect(url_for("novo"))

        cursor.execute("""
            INSERT INTO livro (nome, autor, ano_publicacao)
            VALUES (?, ?, ?)
            returning id_livro
        """, (nome, autor, ano_publicado))

        id_livro = cursor.fetchone()[0]

        con.commit()

        arquivo = request.files['imagem']

        if arquivo:
            arquivo.save(f'uploads/capa{id_livro}.jpg')

        flash("Livro cadastrado com sucesso!")

    except Exception as e:

        flash(f"Ocorreu um erro -> {e}")
        con.rollback()

    finally:

        cursor.close()

    return redirect(url_for("index"))


@app.route("/editar/<int:id>", methods=['GET', 'POST'])
def editar(id):
    cursor = con.cursor()
    try:
        cursor.execute("""SELECT id_livro, nome, autor, ano_publicacao
                          from livro
                          where id_livro = ? """, (id,))
        livro = cursor.fetchone()

        if not livro:
            flash('Livro não encontrado!')
            return redirect(url_for("index"))

        if request.method == 'POST':
            nome = request.form['titulo']
            autor = request.form['autor']
            ano_publicacao = request.form['ano_publicado']
            print('entrei')

            cursor.execute(""" UPDATE livro
                               set nome           = ?,
                                   autor          = ?,
                                   ano_publicacao = ?
                               where id_livro = ?""", (nome, autor, ano_publicacao, id))

            print('alterei')

            con.commit()
            flash("Livro editado com sucesso!")
            return redirect(url_for("index"))

        return render_template("editar.html", livro=livro)

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro -> {e}")
        return redirect(url_for("index"))
    finally:
        cursor.close()


@app.route("/deletar/<int:id>", methods=['POST'])
def deletar(id):
    cursor = con.cursor()
    try:
        cursor.execute("""DELETE
                          FROM livro
                          where id_livro = ?""", (id,))
        con.commit()
        flash("Livro deletado com sucesso!")
        return redirect(url_for("index"))
    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro -> {e}")
        return redirect(url_for("index"))
    finally:
        cursor.close()


@app.route("/listar_usu")
def lista_usu():
    cursor = con.cursor()  # abrindo o cursor
    cursor.execute("""select u.id_usuario, u.nome, u.email, u.senha
                      from usuario u
                      order by u.nome""")

    usuarios = cursor.fetchall()

    cursor.close()

    return render_template('listar_usu.html', usuarios=usuarios)


@app.route("/usu_novo")
def usu_novo():
    return render_template('usu_novo.html')


@app.route("/criastes", methods=['POST'])
def criastes():
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']

    if not senha_forte(senha):
        flash('A senha precisa ter no minimo 8 caracteres, uma letra maiuscula e uma minuscula')
        return redirect(url_for('usu_novo'))


    cursor = con.cursor()

    try:
        senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

        cursor.execute("""
            INSERT INTO usuario (nome, email, senha)
            VALUES (?, ?, ?)
        """, (nome, email, senha_hash))

        con.commit()

        flash("Usuário cadastrado com sucesso!", "success")
    except Exception as e:
        con.rollback()
        flash(f"Erro ao cadastrar usuário: {e}", "danger")
    finally:
        cursor.close()

    return redirect(url_for('lista_usu'))

@app.route("/editares/<int:id>",methods=['GET','POST'])
def editares(id):

    cursor = con.cursor()
    try:
        cursor.execute("""SELECT id_usuario,nome,email,senha
                          from usuario
                          where id_usuario = ? """, (id,))
        usuario = cursor.fetchone()

        if not usuario:
            flash('Usuario não encontrado!')
            return redirect(url_for("lista_usu"))

        if request.method == 'POST':
            nome = request.form['nome']
            email = request.form['email']
            senha = request.form['senha']
            print('entrei')

            cursor.execute(""" UPDATE usuario
                               set nome = ?, email = ?, senha = ?
                               where id_usuario = ?""",
                           (nome,email,senha,id))

            print('alterei')

            con.commit()
            flash("Usuario editado com sucesso!")
            return redirect(url_for("lista_usu"))

        return render_template("usu_editar.html", usuario=usuario)

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro -> {e}")
        return redirect(url_for("lista_usu"))
    finally:
        cursor.close()

@app.route("/deletar_usu/<int:id>", methods=['POST'])
def deletar_usu(id):
    cursor = con.cursor()
    try:
        cursor.execute("""DELETE FROM usuario where id_usuario = ?""", (id,))
        con.commit()
        flash("Usuario deletado com sucesso!")
        return redirect(url_for("lista_usu"))
    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro -> {e}")
        return redirect(url_for("lista_usu"))
    finally:
        cursor.close()


@app.route('/login', methods=['POST', 'GET'])
def login():

    if request.method == 'GET':
        return render_template('login.html')


    email = request.form.get('email')
    senha = request.form.get('senha')

    cursor = con.cursor()

    try:

        cursor.execute("""
                       SELECT id_usuario, senha
                       FROM usuario
                       WHERE email = ?
                       """, (email,))

        usuario = cursor.fetchone()

        if not usuario:
            flash("Usuário não encontrado")
            return redirect(url_for('login'))


        id_usuario, senha_hash = usuario

        if bcrypt.check_password_hash(senha_hash, senha):
            session['id_usuario'] = id_usuario
            flash('Conta logada com sucesso')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha inválida')
            return redirect(url_for('login'))

    except Exception as e:
        flash(f"Ocorreu um erro -> {e}")
        return redirect(url_for("login"))

    finally:
        cursor.close()

@app.route('/logout')
def logout():
    session.pop('id_usuario', None)
    flash("Logout com sucesso!")
    return redirect(url_for('login'))

def senha_forte(senha):
    if len(senha) < 8:
        return False
    elif senha.islower(): #letra maiuscula
        return False
    elif senha.isalpha(): #letra minuscula
        return False
    elif senha.isdigit(): #caractere especial
        return False
    else:
        return True

if __name__ == "__main__":
    app.run(debug=True)
