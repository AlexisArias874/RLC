# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Serie(db.Model):
    __tablename__ = 'serie'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False, unique=True)
    descripcion = db.Column(db.Text, nullable=True)
    poster_url = db.Column(db.String(300), nullable=True) # URL de la imagen del póster
    fecha_lanzamiento = db.Column(db.Date, nullable=True)
    temporadas = db.relationship('Temporada', backref='serie', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Serie {self.titulo}>"

class Temporada(db.Model):
    __tablename__ = 'temporada'
    id = db.Column(db.Integer, primary_key=True)
    numero_temporada = db.Column(db.Integer, nullable=False)
    titulo_temporada = db.Column(db.String(150), nullable=True)
    serie_id = db.Column(db.Integer, db.ForeignKey('serie.id'), nullable=False)
    episodios = db.relationship('Episodio', backref='temporada', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Temporada {self.numero_temporada} de {self.serie.titulo if self.serie else 'Serie Desconocida'}>"

class Episodio(db.Model):
    __tablename__ = 'episodio'
    id = db.Column(db.Integer, primary_key=True)
    numero_episodio = db.Column(db.Integer, nullable=False)
    titulo_episodio = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    url_video = db.Column(db.String(500), nullable=False) # URL del video de Vimeo (ej: https://vimeo.com/VIDEO_ID)
    duracion_minutos = db.Column(db.Integer, nullable=True)
    temporada_id = db.Column(db.Integer, db.ForeignKey('temporada.id'), nullable=False)

    def __repr__(self):
        return f"<Episodio {self.numero_episodio}: {self.titulo_episodio}>"

    def get_vimeo_id(self):
        # Intenta extraer el ID del video de Vimeo de la URL
        # Asume formato como https://vimeo.com/123456789 o https://player.vimeo.com/video/123456789
        if 'vimeo.com/' in self.url_video:
            parts = self.url_video.split('/')
            return parts[-1].split('?')[0] # Maneja parámetros en la URL
        return None