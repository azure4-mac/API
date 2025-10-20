from flask import request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import os
import functools

from app import db
from app.models import Usuario, Professor, Escola, Campeonato, Liga, Questao, Conquista

# =====================================================
# CONFIG
# =====================================================
SECRET_KEY = os.getenv("SECRET_KEY", "CHAVE_SUPER_SECRETA_DEV")

# =====================================================
# JWT Middleware
# =====================================================
def jwt_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Token ausente ou inválido"}), 401
        token = auth_header.split(" ")[1]
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token inválido"}), 401
        return func(*args, **kwargs)
    return wrapper

from uuid import uuid4

# =====================================================
# ROTAS
# =====================================================

def init_routes(app):
    # =====================================================
    # ============== TESTE CRIAR ESCOLA ===================
    # =====================================================

    @app.route('/api/escolas', methods=['GET'])
    def listar_escolas():
        escolas = Escola.query.all()
        return jsonify({
            'status': True,
            'escolas': [e.to_dict() for e in escolas]
        }), 200

    @app.route('/api/escola/criar', methods=['POST'])
    def criar_escola_com_tokens():
        """
        Cria uma escola pré-cadastrada e gera tokens de professor/aluno.
        Espera JSON: { "nome": "Escola X" }
        """
        data = request.get_json() or {}
        nome = data.get('nome')
        if not nome:
            return jsonify({'status': False, 'message': 'Nome da escola é obrigatório.'}), 400

        # gera tokens únicos
        teachercode = str(uuid4())[:8]
        studentcode = str(uuid4())[:8]

        escola = Escola(
            nick=nome,
            teachercode=teachercode,
            studentcode=studentcode
        )
        db.session.add(escola)
        db.session.commit()

        return jsonify({
            'status': True,
            'message': 'Escola criada com sucesso!',
            'escola': {
                'id': escola.id,
                'nome': escola.nick,
                'teachercode': escola.teachercode,
                'studentcode': escola.studentcode
            }
        }), 201



    # -----------------------
    # INDEX
    # -----------------------
    @app.route('/')
    def index():
        return jsonify({"status": "API Flask rodando!"}), 200


    # =====================================================
    # ============== AUTENTICAÇÃO ==========================
    # =====================================================

    # ---------- REGISTRO ----------
    @app.route('/api/register', methods=['POST'])
    def register_usuario():
        """
        Cadastro de usuário (aluno ou professor).
        Espera JSON: { "email": "...", "senha": "...", "nick": "...", "school_code": "..." }
        """
        data = request.get_json() or {}

        email = data.get('email')
        senha = data.get('senha')
        nick = data.get('nick')
        school_code = data.get('school_code')

        if not all([email, senha, nick, school_code]):
            abort(400, description="Faltam dados (email, senha, nick, school_code).")

        # Verifica duplicidade
        if Usuario.query.filter_by(email=email).first() or Professor.query.filter_by(email=email).first():
            abort(409, description="Email já cadastrado.")
        if Usuario.query.filter_by(nick=nick).first():
            abort(409, description="Nick já cadastrado.")

        # Verifica se o código corresponde a alguma escola
        escola = Escola.query.filter(
            (Escola.teachercode == school_code) | (Escola.studentcode == school_code)
        ).first()

        if not escola:
            return jsonify({'status': False, 'message': 'Código de escola inválido.'}), 400

        hashed = generate_password_hash(senha)

        # Decide tipo de usuário conforme o código
        if escola.teachercode == school_code:
            novo = Professor(email=email, senha=hashed, nome=nick, escola_id=escola.id)
            role = "professor"
        else:
            novo = Usuario(email=email, senha=hashed, nick=nick, escola_id=escola.id)
            role = "aluno"

        db.session.add(novo)
        db.session.commit()

        return jsonify({
            "status": True,
            "message": f"{role.capitalize()} criado com sucesso!",
            "role": role,
            "user": novo.to_dict()
        }), 201

    # ---------- LOGIN ----------
    @app.route('/api/login', methods=['POST'])
    def login():
        """
        Espera JSON: { "email": "...", "senha": "..." }
        Retorna token JWT + dados do usuário
        """
        data = request.get_json() or {}
        email = data.get('email')
        senha = data.get('senha')

        if not all([email, senha]):
            return jsonify({"status": False, "message": "Email e senha obrigatórios."}), 400

        user = Usuario.query.filter_by(email=email).first()
        prof = Professor.query.filter_by(email=email).first()

        conta = user or prof
        tipo = "usuario" if user else ("professor" if prof else None)

        if not conta or not check_password_hash(conta.senha, senha):
            return jsonify({"status": False, "message": "Credenciais inválidas."}), 401

        payload = {
            "id": conta.id,
            "email": conta.email,
            "nick": getattr(conta, "nick", None),
            "user_type": tipo,
            "exp": datetime.utcnow() + timedelta(hours=6)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify({
            "status": True,
            "token": token,
            "user_type": tipo,
            "user_data": conta.to_dict()
        }), 200


    # =====================================================
    # ============== ESCOLAS ===============================
    # =====================================================
    @app.route('/api/escola', methods=['POST'])
    @jwt_required
    def criar_escola():
        """
        Cria uma nova escola (somente professores)
        Espera JSON: { "nome": "...", "cod_entrada": "..." }
        """
        user = request.user
        if user.get('user_type') != 'professor':
            return jsonify({'erro': 'Apenas professores podem criar escolas.'}), 403

        data = request.get_json() or {}
        nome = data.get('nome')
        cod = data.get('cod_entrada')

        if not nome:
            return jsonify({'erro': 'Nome da escola obrigatório.'}), 400

        # Cria a escola
        escola = Escola(nick=nome, cod_entrada=cod)
        db.session.add(escola)
        db.session.commit()

        # Vincula o professor criador
        prof = Professor.query.get(user.get('id'))
        if prof and escola not in prof.escolas:
            prof.escolas.append(escola)
            db.session.commit()

        return jsonify({
            'status': True,
            'message': 'Escola criada com sucesso.',
            'escola': escola.to_dict()
        }), 201


    @app.route('/api/escola/join', methods=['POST'])
    @jwt_required
    def join_escola():
        """
        Aluno entra em escola via código.
        Espera JSON: { "cod_entrada": "..." }
        """
        user = request.user
        if user.get('user_type') != 'usuario':
            return jsonify({'erro': 'Apenas alunos podem entrar em escolas.'}), 403

        data = request.get_json() or {}
        cod = data.get('cod_entrada')
        if not cod:
            return jsonify({'erro': 'Código de entrada necessário.'}), 400

        escola = Escola.query.filter_by(cod_entrada=cod).first()
        if not escola:
            return jsonify({'erro': 'Código inválido.'}), 404

        aluno = Usuario.query.get(user.get('id'))
        if escola not in aluno.escolas:
            aluno.escolas.append(escola)
            db.session.commit()

        return jsonify({'status': True, 'message': f'Aluno vinculado à escola {escola.nick}.'}), 200


    @app.route('/api/escola/<int:escola_id>', methods=['GET'])
    @jwt_required
    def get_escola(escola_id):
        """
        Retorna detalhes da escola (professores e alunos).
        """
        escola = Escola.query.get(escola_id)
        if not escola:
            return jsonify({'erro': 'Escola não encontrada'}), 404

        professores = [p.to_dict() for p in escola.professores]
        alunos = [a.to_dict() for a in escola.alunos]

        return jsonify({
            'status': True,
            'escola': escola.to_dict(),
            'professores': professores,
            'alunos': alunos
        }), 200


    # =====================================================
    # ============== LIGAS, QUESTÕES, CAMPEONATOS =========
    # =====================================================
    @app.route('/api/ligas', methods=['POST'])
    @jwt_required
    def criar_liga():
        data = request.get_json() or {}
        nome = data.get('nome')
        if not nome:
            return jsonify({'erro': 'Nome é obrigatório.'}), 400
        liga = Liga(nome=nome)
        db.session.add(liga)
        db.session.commit()
        return jsonify({'status': True, 'liga': liga.to_dict()}), 201


    @app.route('/api/questao', methods=['POST'])
    @jwt_required
    def criar_questao():
        user = request.user
        data = request.get_json() or {}
        materia = data.get('materia')
        texto = data.get('texto')
        questao = Questao(usuario_id=user.get('id'), materia=materia, texto=texto)
        db.session.add(questao)
        db.session.commit()
        return jsonify({'status': True, 'questao': questao.to_dict()}), 201


    @app.route('/api/campeonato', methods=['POST'])
    @jwt_required
    def criar_campeonato():
        user = request.user
        if user.get('user_type') != 'professor':
            return jsonify({'erro': 'Apenas professores podem criar campeonatos.'}), 403
        data = request.get_json() or {}
        nome = data.get('nome')
        if not nome:
            return jsonify({'erro': 'Nome obrigatório.'}), 400
        campeonato = Campeonato(nome=nome, criador_id=user.get('id'))
        db.session.add(campeonato)
        db.session.commit()
        return jsonify({'status': True, 'campeonato': campeonato.to_dict()}), 201

    # =====================================================
    # ============== LISTAGEM DE CAMPEONATOS ===============
    # =====================================================
    @app.route('/api/campeonato', methods=['GET'])
    @jwt_required
    def listar_campeonatos():
        """
        Retorna todos os campeonatos cadastrados.
        """
        campeonatos = Campeonato.query.all()
        return jsonify({
            "status": True,
            "campeonatos": [c.to_dict() for c in campeonatos]
        }), 200


    # =====================================================
    # ============== LISTAGEM DE LIGAS =====================
    # =====================================================
    @app.route('/api/ligas', methods=['GET'])
    @jwt_required
    def listar_ligas():
        """
        Retorna todas as ligas cadastradas.
        """
        ligas = Liga.query.all()
        return jsonify({
            "status": True,
            "ligas": [l.to_dict() for l in ligas]
        }), 200


    # =====================================================
    # ============== LISTAGEM DE QUESTÕES ==================
    # =====================================================
    @app.route('/api/questao', methods=['GET'])
    @jwt_required
    def listar_questoes():
        """
        Retorna todas as questões cadastradas.
        """
        questoes = Questao.query.all()
        return jsonify({
            "status": True,
            "questoes": [q.to_dict() for q in questoes]
        }), 200

    @app.route("/api/me", methods=["GET"])
    def me():
        # lógica para retornar os dados do usuário logado
        return {"user": Usuario.to_dict()}
