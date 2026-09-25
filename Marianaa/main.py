from flask import Flask, render_template, request, flash, redirect, url_for,session,send_file
import fdb
from flask_bcrypt import Bcrypt
from fpdf import FPDF
app = Flask(__name__)

bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'Aqui_é_a_chave_da_turma_a '


host = "localhost"
database = r"C:\Users\Aluno\Downloads\BANCO.FDB"
user = 'sysdba'
password = 'sysdba'

con = fdb.connect(host=host, database=database, user=user, password=password)


@app.route("/biblioteca")
def biblioteca():
    cursor = con.cursor()  # abrindo o cursor
    cursor.execute("""select l.id_livro, l.nome, l.autor, l.ano_publicacao
                      from livro l
                      order by l.nome""")

    livros = cursor.fetchall()

    cursor.close()

    return render_template('biblioteca.html', livros=livros)


@app.route("/novo")
def novo():
    if 'id_usuario' not in session:
        flash('Precisa estar logado')
        return redirect(url_for("index"))
    return render_template('novo.html',titulo="Novo Livro")

@app.route("/criar", methods=['POST','GET'])
def criar():
    if request.method == 'GET':
        return render_template('novo.html')

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

    return redirect(url_for("biblioteca"))


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
            return redirect(url_for("biblioteca"))

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
            return redirect(url_for("biblioteca"))

        return render_template("editar.html", livro=livro)

    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro -> {e}")
        return redirect(url_for("biblioteca"))
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
        return redirect(url_for("biblioteca"))
    except Exception as e:
        con.rollback()
        flash(f"Ocorreu um erro -> {e}")
        return redirect(url_for("biblioteca"))
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
            INSERT INTO usuario (nome, email, senha,tentativas)
            VALUES (?, ?, ?,?)
        """, (nome, email, senha_hash,0))

        con.commit()

        flash("Usuário cadastrado com sucesso!", "success")
    except Exception as e:
        con.rollback()
        flash(f"Erro ao cadastrar usuário: {e}", "danger")
    finally:
        cursor.close()

    return redirect(url_for('index'))

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

            if not senha_forte(senha):
                flash('A senha precisa ter no minimo 8 caracteres, uma letra maiuscula e uma minuscula')
                return redirect(url_for('usu_novo'))

            senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

            cursor.execute(""" UPDATE usuario
                               set nome = ?, email = ?, senha = ?
                               where id_usuario = ?""",
                           (nome,email,senha_hash,id))



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


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    email = request.form['email']
    senha = request.form['senha']
    cursor = con.cursor()
    try:
        cursor.execute("""SELECT id_usuario, senha, tentativas
                          FROM usuario u
                          WHERE u.email = ? """, (email,))
        usuario = cursor.fetchone()
        if not usuario:
            flash("Usuário não encontrado")
            return redirect(url_for('index'))
        id_usuario, senha_hash, tentativas = usuario

        if tentativas >= 3:
            flash("Você passou de 3 tentativas! Sua conta foi bloqueada.")
            return redirect(url_for('index'))
        if usuario:
            if bcrypt.check_password_hash(senha_hash, senha):

                cursor.execute("""UPDATE usuario
                                  set tentativas = 0
                                  where id_usuario = ?""", (id_usuario,))
                con.commit()
                session['id_usuario'] = id_usuario
                flash('Conta logada')
                return redirect(url_for('biblioteca'))
            else:

                cursor.execute("""UPDATE usuario
                                  set tentativas = tentativas + 1
                                  where id_usuario = ?""", (id_usuario,))
                con.commit()
                if tentativas + 1 >= 3:
                    flash('Você passou de 3 tentativas! Sua conta foi bloqueada.')
                else:
                    flash('Email ou senha inválida')
                return redirect(url_for('index'))
        return render_template('index.html')

    except Exception as e:
        flash(f"Ocorreu um error -> {e}")
        con.rollback()
        return redirect(url_for('index'))
    finally:
        cursor.close()



@app.route('/logout')
def logout():
    if 'id_usuario' in session:
        session.pop('id_usuario')
        flash("Logout com sucesso!")
        return redirect(url_for('biblioteca'))

    else:
        flash('Nenhuma conta está logada')
        return redirect(url_for('index'))


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


@app.route('/livros/relatorio', methods=['GET'])
def relatorio():

    cursor = con.cursor()

    cursor.execute("""
        SELECT id_livro, nome, autor, ano_publicacao
        FROM livro
    """)

    livros = cursor.fetchall()
    cursor.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Relatório de Livros", ln=True, align='C')

    pdf.ln(5)  # Espaço entre o título e a linha
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())  # Linha abaixo do título
    pdf.ln(5)  # Espaço após a linha

    pdf.set_font("Arial", size=12)

    for livro in livros:
        pdf.cell(
            200,
            10,
            f"ID: {livro[0]} - {livro[1]} - {livro[2]} - {livro[3]}",
            ln=True
        )

    contador_livros = len(livros)

    pdf.ln(10)  # Espaço antes do contador

    pdf.set_font("Arial", style='B', size=12)

    pdf.cell(
        200,
        10,
        f"Total de livros cadastrados: {contador_livros}",
        ln=True,
        align='C'
    )

    pdf_path = "relatorio_livros.pdf"

    pdf.output(pdf_path)

    return send_file(
        pdf_path,
        as_attachment=True,
        mimetype='application/pdf'
    )

if __name__ == "__main__":
    app.run(debug=True)
