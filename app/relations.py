from app import db

# Associação Usuários <-> Campeonatos
usuarios_campeonatos = db.Table(
    'usuarios_campeonatos',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('campeonato_id', db.Integer, db.ForeignKey('campeonato.id'), primary_key=True)
)

# Associação Usuários <-> Liga
usuarios_liga = db.Table(
    'usuarios_liga',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('liga_id', db.Integer, db.ForeignKey('liga.id'), primary_key=True)
)

# Associação Usuários <-> Questões (por exemplo: questões respondidas / favorited)
usuarios_questoes = db.Table(
    'usuarios_questoes',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('questao_id', db.Integer, db.ForeignKey('questao.id'), primary_key=True)
)

# Associação Questões <-> Campeonato
questoes_campeonato = db.Table(
    'questoes_campeonato',
    db.Column('questao_id', db.Integer, db.ForeignKey('questao.id'), primary_key=True),
    db.Column('campeonato_id', db.Integer, db.ForeignKey('campeonato.id'), primary_key=True)
)

# Associação Questões <-> Liga
questoes_liga = db.Table(
    'questoes_liga',
    db.Column('questao_id', db.Integer, db.ForeignKey('questao.id'), primary_key=True),
    db.Column('liga_id', db.Integer, db.ForeignKey('liga.id'), primary_key=True)
)

# Associação Usuários <-> Conquista
usuario_conquista = db.Table(
    'usuario_conquista',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('conquista_id', db.Integer, db.ForeignKey('conquista.id'), primary_key=True)
)

# Associação Professor <-> Escola
professor_escola = db.Table(
    'professor_escola',
    db.Column('professor_id', db.Integer, db.ForeignKey('professor.id'), primary_key=True),
    db.Column('escola_id', db.Integer, db.ForeignKey('escola.id'), primary_key=True)
)

# Associação Usuario <-> Escola (alunos matriculados)
usuario_escola = db.Table(
    'usuario_escola',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('escola_id', db.Integer, db.ForeignKey('escola.id'), primary_key=True)
)

# Amigos (usuários conectados)
amigos = db.Table(
    'amigos',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id')),
    db.Column('amigo_id', db.Integer, db.ForeignKey('usuario.id'))
)
