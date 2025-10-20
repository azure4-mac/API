from app import db
from app.relations import (
    usuarios_campeonatos, usuarios_liga,
    usuarios_questoes, questoes_campeonato,
    questoes_liga, usuario_conquista,
    professor_escola, usuario_escola  # 🔹 ADIÇÃO
)
from datetime import datetime

# ---------------------------
# Model: Usuario
# ---------------------------
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(200))
    nick = db.Column(db.String(50))
    nivel = db.Column(db.String(50), default='usuario')
    ofensiva = db.Column(db.Integer, default=0) 



    # relações    
    escola_id = db.Column(db.Integer, db.ForeignKey('escola.id'))
    campeonatos = db.relationship('Campeonato', secondary=usuarios_campeonatos, back_populates='usuarios')
    ligas = db.relationship('Liga', secondary=usuarios_liga, back_populates='usuarios')
    questoes = db.relationship('Questao', secondary=usuarios_questoes, back_populates='usuarios')
    conquistas = db.relationship('Conquista', secondary=usuario_conquista, back_populates='usuarios')
    escolas = db.relationship('Escola', secondary=usuario_escola, back_populates='alunos')  # 🔹 ADIÇÃO

    def to_dict(self):
            return {
                "id": self.id,
                "email": self.email,
                "nick": self.nick,
                "nivel": self.nivel,
                "ofensiva": self.ofensiva
            }


# ---------------------------
# Model: Professor
# ---------------------------
class Professor(db.Model):
    __tablename__ = 'professor'
    escola_id = db.Column(db.Integer, db.ForeignKey('escola.id'))
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    atuacao = db.Column(db.String(100), nullable=True)
    disciplina = db.Column(db.String(100), nullable=True)

    escolas = db.relationship('Escola', secondary=professor_escola, back_populates='professores')

    def to_dict(self):
        return {
            "id": self.id,
            "nick": self.nick,
            "email": self.email,
            "atuacao": self.atuacao,
            "disciplina": self.disciplina
        }


# ---------------------------
# Model: Escola
# ---------------------------
class Escola(db.Model):
    __tablename__ = 'escola'
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    senha = db.Column(db.String(255), nullable=True)
    atuacao = db.Column(db.String(100), nullable=True)
    cod_entrada = db.Column(db.String(50), nullable=True)

    # 🔹 Códigos exclusivos para cadastro
    teachercode = db.Column(db.String(50), unique=True, nullable=True)
    studentcode = db.Column(db.String(50), unique=True, nullable=True)

    professores = db.relationship('Professor', secondary=professor_escola, back_populates='escolas')
    alunos = db.relationship('Usuario', secondary=usuario_escola, back_populates='escolas')

    def to_dict(self):
        return {
            "id": self.id,
            "nick": self.nick,
            "email": self.email,
            "cod_entrada": self.cod_entrada,
            "teachercode": self.teachercode,
            "studentcode": self.studentcode,
        }



# ---------------------------
# Model: Turma
# ---------------------------
class Turma(db.Model):
    __tablename__ = 'turma'
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String(100), nullable=True)
    senha = db.Column(db.String(255), nullable=True)
    atuacao = db.Column(db.String(100), nullable=True)
    disciplina = db.Column(db.String(100), nullable=True)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=True)


# ---------------------------
# Model: Campeonato
# ---------------------------
class Campeonato(db.Model):
    __tablename__ = 'campeonato'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    conquista = db.Column(db.String(255), nullable=True)
    pontos = db.Column(db.Integer, default=0)
    senha = db.Column(db.String(255), nullable=True)
    criador_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=True)

    usuarios = db.relationship('Usuario', secondary=usuarios_campeonatos, back_populates='campeonatos')
    questoes = db.relationship('Questao', secondary=questoes_campeonato, back_populates='campeonatos')

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "conquista": self.conquista,
            "pontos": self.pontos,
            "criador_id": self.criador_id
        }


# ---------------------------
# Model: Liga
# ---------------------------
class Liga(db.Model):
    __tablename__ = 'liga'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)

    usuarios = db.relationship('Usuario', secondary=usuarios_liga, back_populates='ligas')
    questoes = db.relationship('Questao', secondary=questoes_liga, back_populates='ligas')

    def to_dict(self):
        return {"id": self.id, "nome": self.nome}


# ---------------------------
# Model: Questao
# ---------------------------
class Questao(db.Model):
    __tablename__ = 'questao'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    materia = db.Column(db.String(255), nullable=True)
    subtopico = db.Column(db.String(255), nullable=True)
    subsubtopico = db.Column(db.String(255), nullable=True)
    texto = db.Column(db.Text, nullable=True)

    usuarios = db.relationship('Usuario', secondary=usuarios_questoes, back_populates='questoes')
    campeonatos = db.relationship('Campeonato', secondary=questoes_campeonato, back_populates='questoes')
    ligas = db.relationship('Liga', secondary=questoes_liga, back_populates='questoes')

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "materia": self.materia,
            "subtopico": self.subtopico,
            "subsubtopico": self.subsubtopico,
            "texto": (self.texto[:200] + "...") if self.texto and len(self.texto) > 200 else self.texto
        }


# ---------------------------
# Model: Conquista
# ---------------------------
class Conquista(db.Model):
    __tablename__ = 'conquista'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    raridade = db.Column(db.String(50), nullable=True)

    usuarios = db.relationship('Usuario', secondary=usuario_conquista, back_populates='conquistas')

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "raridade": self.raridade}


# ---------------------------
# Model: Amigos
# ---------------------------
class Amigo(db.Model):
    __tablename__ = 'amigo'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    amigo_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
