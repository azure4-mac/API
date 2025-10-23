from flask import request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt, os, functools
from uuid import uuid4

from app import db
from app.models import Usuario, Professor, Escola, Campeonato, Liga, Questao

# ================= CONFIG =================
SECRET_KEY = os.getenv("SECRET_KEY", "CHAVE_SUPER_SECRETA_DEV")

# ================= JWT Middleware =================
def jwt_required(func):
    """Valida o token JWT em rotas protegidas"""
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


# ================= ROTAS =================
def init_routes(app):

    # -------- ESCOLAS --------
    @app.route('/api/escolas', methods=['GET'])
    def listar_escolas():
        """Lista todas as escolas"""
        escolas = Escola.query.all()
        return jsonify({
            'status': True,
            'escolas': [e.to_dict() for e in escolas]
        }), 200

    @app.route('/api/escola/criar', methods=['POST'])
    def criar_escola_com_tokens():
        """Cria escola e gera códigos de acesso"""
        data = request.get_json() or {}
        nome = data.get('nome')
        if not nome:
            return jsonify({'status': False, 'message': 'Nome da escola é obrigatório.'}), 400

        escola = Escola(
            nick=nome,
            code_escola=str(uuid4())[:8],
            teachercode=str(uuid4())[:8],
            studentcode=str(uuid4())[:8]
        )
        db.session.add(escola)
        db.session.commit()

        return jsonify({
            'status': True,
            'message': 'Escola criada com sucesso!',
            'escola': escola.to_dict()
        }), 201

    @app.route('/api/escola/<int:escola_id>', methods=['GET'])
    def get_escola(escola_id):
        """Detalha uma escola e seus membros"""
        escola = Escola.query.get(escola_id)
        if not escola:
            return jsonify({'erro': 'Escola não encontrada'}), 404

        return jsonify({
            'status': True,
            'escola': escola.to_dict(),
            'professores': [p.to_dict() for p in escola.professores],
            'alunos': [a.to_dict() for a in escola.alunos]
        }), 200


    # -------- INDEX --------
    @app.route('/')
    def index():
        """Rota base da API"""
        return jsonify({"status": "API Flask rodando!"}), 200


    # -------- REGISTRO --------
    @app.route('/api/register', methods=['POST'])
    def register_usuario():
        """Registra novo aluno ou professor"""
        data = request.get_json() or {}
        email, senha, nick, school_code = (
            data.get('email'),
            data.get('senha'),
            data.get('nick'),
            data.get('school_code'),
        )

        if not all([email, senha, nick, school_code]):
            abort(400, description="Faltam dados (email, senha, nick, school_code).")

        if Usuario.query.filter_by(email=email).first() or Professor.query.filter_by(email=email).first():
            abort(409, description="Email já cadastrado.")
        if Usuario.query.filter_by(nick=nick).first():
            abort(409, description="Nick já cadastrado.")

        escola = Escola.query.filter(
            (Escola.teachercode == school_code) | (Escola.studentcode == school_code)
        ).first()
        if not escola:
            return jsonify({'status': False, 'message': 'Código de escola inválido.'}), 400

        hashed = generate_password_hash(senha)
        if escola.teachercode == school_code:
            novo = Professor(email=email, senha=hashed, nick=nick, escola_id=escola.id)
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


    # -------- LOGIN --------
    @app.route('/api/login', methods=['POST'])
    def login():
        """Autentica usuário e retorna token"""
        data = request.get_json() or {}
        email, senha = data.get('email'), data.get('senha')

        if not all([email, senha]):
            return jsonify({"status": False, "message": "Email e senha obrigatórios."}), 400

        user = Usuario.query.filter_by(email=email).first()
        prof = Professor.query.filter_by(email=email).first()
        conta = user or prof
        tipo = "usuario" if user else ("professor" if prof else None)

        if not conta or not check_password_hash(conta.senha, senha):
            return jsonify({"status": False, "message": "Credenciais inválidas."}), 401

        escola = Escola.query.get(conta.escola_id) if conta.escola_id else None
        nome_escola = escola.nick if escola else None

        payload = {
            "id": conta.id,
            "email": conta.email,
            "nick": conta.nick,
            "user_type": tipo,
            "escola": nome_escola,
            "exp": datetime.utcnow() + timedelta(hours=6)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify({
            "status": True,
            "token": token,
            "user_type": tipo,
            "user_data": conta.to_dict(),
            "escola": nome_escola
        }), 200


    # -------- LIGAS --------
    @app.route('/api/ligas', methods=['POST'])
    @jwt_required
    def criar_liga():
        """Cria nova liga"""
        data = request.get_json() or {}
        nome = data.get('nome')
        if not nome:
            return jsonify({'erro': 'Nome é obrigatório.'}), 400
        liga = Liga(nome=nome)
        db.session.add(liga)
        db.session.commit()
        return jsonify({'status': True, 'liga': liga.to_dict()}), 201

    @app.route('/api/ligas', methods=['GET'])
    @jwt_required
    def listar_ligas():
        """Lista todas as ligas"""
        ligas = Liga.query.all()
        return jsonify({"status": True, "ligas": [l.to_dict() for l in ligas]}), 200


    # -------- QUESTÕES --------
    @app.route('/api/questao', methods=['POST'])
    @jwt_required
    def criar_questao():
        """Cria nova questão"""
        user = request.user
        data = request.get_json() or {}
        questao = Questao(usuario_id=user.get('id'),
                          materia=data.get('materia'),
                          texto=data.get('texto'))
        db.session.add(questao)
        db.session.commit()
        return jsonify({'status': True, 'questao': questao.to_dict()}), 201

    @app.route('/api/questao', methods=['GET'])
    @jwt_required
    def listar_questoes():
        """Lista todas as questões"""
        questoes = Questao.query.all()
        return jsonify({"status": True, "questoes": [q.to_dict() for q in questoes]}), 200


    # -------- CAMPEONATOS --------
    @app.route('/api/campeonato', methods=['POST'])
    @jwt_required
    def criar_campeonato():
        """Cria novo campeonato (somente professor)"""
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

    @app.route('/api/campeonato', methods=['GET'])
    @jwt_required
    def listar_campeonatos():
        """Lista todos os campeonatos"""
        campeonatos = Campeonato.query.all()
        return jsonify({"status": True, "campeonatos": [c.to_dict() for c in campeonatos]}), 200


    # -------- PERFIL LOGADO --------
    @app.route("/api/me", methods=["GET"])
    @jwt_required
    def me():
        """Retorna dados do usuário logado e da escola"""
        user_data = request.user
        user_id, user_type = user_data.get("id"), user_data.get("user_type")

        user = Professor.query.get(user_id) if user_type == "professor" else Usuario.query.get(user_id)
        if not user:
            return jsonify({"status": False, "message": "Usuário não encontrado"}), 404

        escola = Escola.query.get(user.escola_id) if user.escola_id else None
        escola_data = {"id": escola.id, "nick": escola.nick} if escola else None

        return jsonify({
            "status": True,
            "user_type": user_type,
            "user": user.to_dict(),
            "escola": escola_data
        }), 200
