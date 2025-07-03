# app.py

import random
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
# ¡IMPORTANTE! Asegúrate de que este archivo 'models.py' exista en la misma carpeta que app.py
from models import db, Serie, Temporada, Episodio 
from datetime import datetime
import os

app = Flask(__name__)

# Configuración de la base de datos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'series_database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu_super_secreto_aqui' # Cambia esto por una clave segura

db.init_app(app)

# --- Rutas de Vista Pública ---
@app.route('/')
def index():
    # Obtiene todas las series para la parrilla aleatoria de la página de inicio
    todas_las_series = Serie.query.all()
    num_series_a_mostrar = min(len(todas_las_series), 6)
    series_aleatorias = []
    if todas_las_series:
        series_aleatorias = random.sample(todas_las_series, num_series_a_mostrar)
    return render_template('index.html', series=series_aleatorias)

@app.route('/explorar')
def explorar_series():
    # Página para ver todas las series en un formato de cuadrícula
    series = Serie.query.order_by(Serie.titulo).all()
    return render_template('explorar_series.html', series=series)

@app.route('/serie/<int:serie_id>')
def serie_detail(serie_id):
    # Página de detalles de una serie, que muestra las temporadas y episodios
    serie = Serie.query.get_or_404(serie_id)
    return render_template('serie_detail.html', serie=serie)


# --- RUTA MODIFICADA Y CORREGIDA ---
@app.route('/play/<int:episodio_id>')
def play_video(episodio_id):
    # 1. Obtener el episodio actual que se quiere reproducir
    episodio_actual = Episodio.query.get_or_404(episodio_id)
    
    # 2. Obtener TODOS los episodios de la misma temporada, ORDENADOS por número
    todos_episodios_ordenados = sorted(
        episodio_actual.temporada.episodios, 
        key=lambda ep: ep.numero_episodio
    )
    
    # 3. Encontrar el índice (la posición) del episodio actual en esa lista ordenada
    indice_actual = -1
    for i, ep in enumerate(todos_episodios_ordenados):
        if ep.id == episodio_actual.id:
            indice_actual = i
            break
            
    # 4. Determinar cuál es el episodio anterior y el siguiente
    episodio_anterior = None
    episodio_siguiente = None
    
    if indice_actual != -1: # Si encontramos el episodio en la lista
        # Hay un episodio anterior si nuestro índice es mayor que 0
        if indice_actual > 0:
            episodio_anterior = todos_episodios_ordenados[indice_actual - 1]
            
        # Hay un episodio siguiente si nuestro índice no es el último de la lista
        if indice_actual < len(todos_episodios_ordenados) - 1:
            episodio_siguiente = todos_episodios_ordenados[indice_actual + 1]

    # 5. Pasar todos los datos a la plantilla
    return render_template(
        'play_video.html', 
        episodio=episodio_actual,
        episodio_anterior=episodio_anterior,
        episodio_siguiente=episodio_siguiente
    )


# --- Rutas de Administración (SIN CAMBIOS) ---
@app.route('/admin')
def admin_dashboard():
    return render_template('admin/admin_dashboard.html')

@app.route('/admin/series')
def manage_series():
    series = Serie.query.order_by(Serie.titulo).all()
    return render_template('admin/manage_series.html', series=series)

@app.route('/admin/serie/add', methods=['GET', 'POST'])
def add_serie():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        poster_url = request.form.get('poster_url')
        fecha_lanzamiento_str = request.form.get('fecha_lanzamiento')
        if not titulo:
            flash('El título es obligatorio.', 'danger')
            return render_template('admin/form_serie.html', action="add")
        fecha_lanzamiento = None
        if fecha_lanzamiento_str:
            try:
                fecha_lanzamiento = datetime.strptime(fecha_lanzamiento_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha de lanzamiento inválido. Usar YYYY-MM-DD.', 'danger')
                return render_template('admin/form_serie.html', action="add", form_data=request.form)
        nueva_serie = Serie(titulo=titulo, descripcion=descripcion, poster_url=poster_url, fecha_lanzamiento=fecha_lanzamiento)
        try:
            db.session.add(nueva_serie)
            db.session.commit()
            flash(f'Serie "{titulo}" agregada exitosamente.', 'success')
            return redirect(url_for('manage_series'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar la serie: {str(e)}', 'danger')
            return render_template('admin/form_serie.html', action="add", form_data=request.form)
    return render_template('admin/form_serie.html', action="add")

@app.route('/admin/serie/edit/<int:serie_id>', methods=['GET', 'POST'])
def edit_serie(serie_id):
    serie = Serie.query.get_or_404(serie_id)
    if request.method == 'POST':
        serie.titulo = request.form.get('titulo')
        serie.descripcion = request.form.get('descripcion')
        serie.poster_url = request.form.get('poster_url')
        fecha_lanzamiento_str = request.form.get('fecha_lanzamiento')
        if not serie.titulo:
            flash('El título es obligatorio.', 'danger')
            return render_template('admin/form_serie.html', action="edit", serie=serie)
        if fecha_lanzamiento_str:
            try:
                serie.fecha_lanzamiento = datetime.strptime(fecha_lanzamiento_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha de lanzamiento inválido. Usar YYYY-MM-DD.', 'danger')
                return render_template('admin/form_serie.html', action="edit", serie=serie)
        else:
            serie.fecha_lanzamiento = None
        try:
            db.session.commit()
            flash(f'Serie "{serie.titulo}" actualizada exitosamente.', 'success')
            return redirect(url_for('manage_series'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la serie: {str(e)}', 'danger')
    return render_template('admin/form_serie.html', action="edit", serie=serie)

@app.route('/admin/serie/delete/<int:serie_id>', methods=['POST'])
def delete_serie(serie_id):
    serie = Serie.query.get_or_404(serie_id)
    try:
        db.session.delete(serie)
        db.session.commit()
        flash(f'Serie "{serie.titulo}" eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la serie: {str(e)}', 'danger')
    return redirect(url_for('manage_series'))

@app.route('/admin/serie/<int:serie_id>/temporada/add', methods=['GET', 'POST'])
def add_temporada(serie_id):
    serie = Serie.query.get_or_404(serie_id)
    if request.method == 'POST':
        numero_temporada = request.form.get('numero_temporada')
        titulo_temporada = request.form.get('titulo_temporada')
        if not numero_temporada:
            flash('El número de temporada es obligatorio.', 'danger')
        else:
            try:
                numero_temporada = int(numero_temporada)
                nueva_temporada = Temporada(numero_temporada=numero_temporada, titulo_temporada=titulo_temporada, serie_id=serie.id)
                db.session.add(nueva_temporada)
                db.session.commit()
                flash(f'Temporada {numero_temporada} agregada a "{serie.titulo}".', 'success')
                return redirect(url_for('serie_detail', serie_id=serie.id))
            except ValueError:
                flash('El número de temporada debe ser un número.', 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al agregar la temporada: {str(e)}', 'danger')
    return render_template('admin/form_temporada.html', action="add", serie=serie)

@app.route('/admin/temporada/<int:temporada_id>/edit', methods=['GET', 'POST'])
def edit_temporada(temporada_id):
    temporada = Temporada.query.get_or_404(temporada_id)
    if request.method == 'POST':
        numero_temporada_str = request.form.get('numero_temporada')
        temporada.titulo_temporada = request.form.get('titulo_temporada')
        if not numero_temporada_str:
             flash('El número de temporada es obligatorio.', 'danger')
        else:
            try:
                temporada.numero_temporada = int(numero_temporada_str)
                db.session.commit()
                flash(f'Temporada actualizada exitosamente.', 'success')
                return redirect(url_for('serie_detail', serie_id=temporada.serie_id))
            except ValueError:
                flash('El número de temporada debe ser un número.', 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar la temporada: {str(e)}', 'danger')
    return render_template('admin/form_temporada.html', action="edit", temporada=temporada, serie=temporada.serie)

@app.route('/admin/temporada/delete/<int:temporada_id>', methods=['POST'])
def delete_temporada(temporada_id):
    temporada = Temporada.query.get_or_404(temporada_id)
    serie_id_redirect = temporada.serie_id
    try:
        db.session.delete(temporada)
        db.session.commit()
        flash(f'Temporada eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la temporada: {str(e)}', 'danger')
    return redirect(url_for('serie_detail', serie_id=serie_id_redirect))

@app.route('/admin/temporada/<int:temporada_id>/episodio/add', methods=['GET', 'POST'])
def add_episodio(temporada_id):
    temporada = Temporada.query.get_or_404(temporada_id)
    if request.method == 'POST':
        numero_episodio = request.form.get('numero_episodio')
        titulo_episodio = request.form.get('titulo_episodio')
        descripcion = request.form.get('descripcion')
        url_video = request.form.get('url_video')
        duracion_minutos_str = request.form.get('duracion_minutos')
        if not numero_episodio or not titulo_episodio or not url_video:
            flash('Número de episodio, título y URL del video son obligatorios.', 'danger')
        else:
            try:
                numero_episodio = int(numero_episodio)
                duracion_minutos = int(duracion_minutos_str) if duracion_minutos_str else None
                nuevo_episodio = Episodio(numero_episodio=numero_episodio, titulo_episodio=titulo_episodio, descripcion=descripcion, url_video=url_video, duracion_minutos=duracion_minutos, temporada_id=temporada.id)
                db.session.add(nuevo_episodio)
                db.session.commit()
                flash(f'Episodio "{titulo_episodio}" agregado a la temporada.', 'success')
                return redirect(url_for('serie_detail', serie_id=temporada.serie_id))
            except ValueError:
                flash('Número de episodio y duración deben ser números.', 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al agregar el episodio: {str(e)}', 'danger')
    return render_template('admin/form_episodio.html', action="add", temporada=temporada)

@app.route('/admin/episodio/<int:episodio_id>/edit', methods=['GET', 'POST'])
def edit_episodio(episodio_id):
    episodio = Episodio.query.get_or_404(episodio_id)
    if request.method == 'POST':
        numero_episodio_str = request.form.get('numero_episodio')
        episodio.titulo_episodio = request.form.get('titulo_episodio')
        episodio.descripcion = request.form.get('descripcion')
        episodio.url_video = request.form.get('url_video')
        duracion_minutos_str = request.form.get('duracion_minutos')
        if not numero_episodio_str or not episodio.titulo_episodio or not episodio.url_video:
            flash('Número de episodio, título y URL del video son obligatorios.', 'danger')
        else:
            try:
                episodio.numero_episodio = int(numero_episodio_str)
                episodio.duracion_minutos = int(duracion_minutos_str) if duracion_minutos_str else None
                db.session.commit()
                flash(f'Episodio "{episodio.titulo_episodio}" actualizado.', 'success')
                return redirect(url_for('serie_detail', serie_id=episodio.temporada.serie_id))
            except ValueError:
                flash('Número de episodio y duración deben ser números.', 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar el episodio: {str(e)}', 'danger')
    return render_template('admin/form_episodio.html', action="edit", episodio=episodio, temporada=episodio.temporada)

@app.route('/admin/episodio/delete/<int:episodio_id>', methods=['POST'])
def delete_episodio(episodio_id):
    episodio = Episodio.query.get_or_404(episodio_id)
    serie_id_redirect = episodio.temporada.serie_id
    try:
        db.session.delete(episodio)
        db.session.commit()
        flash(f'Episodio "{episodio.titulo_episodio}" eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el episodio: {str(e)}', 'danger')
    return redirect(url_for('serie_detail', serie_id=serie_id_redirect))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)