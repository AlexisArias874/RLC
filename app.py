# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
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
    series = Serie.query.order_by(Serie.titulo).all()
    return render_template('index.html', series=series)

@app.route('/serie/<int:serie_id>')
def serie_detail(serie_id):
    serie = Serie.query.get_or_404(serie_id)
    return render_template('serie_detail.html', serie=serie)

@app.route('/play/<int:episodio_id>')
def play_video(episodio_id):
    episodio = Episodio.query.get_or_404(episodio_id)
    vimeo_id = episodio.get_vimeo_id()
    if not vimeo_id:
        flash('URL de video no válida o no es de Vimeo.', 'danger')
        return redirect(url_for('serie_detail', serie_id=episodio.temporada.serie_id))
    return render_template('play_video.html', episodio=episodio, vimeo_id=vimeo_id)

# --- Rutas de Administración ---
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

        nueva_serie = Serie(
            titulo=titulo, 
            descripcion=descripcion, 
            poster_url=poster_url,
            fecha_lanzamiento=fecha_lanzamiento
        )
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
                nueva_temporada = Temporada(
                    numero_temporada=numero_temporada,
                    titulo_temporada=titulo_temporada,
                    serie_id=serie.id
                )
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
        url_video = request.form.get('url_video') # URL de Vimeo
        duracion_minutos_str = request.form.get('duracion_minutos')

        if not numero_episodio or not titulo_episodio or not url_video:
            flash('Número de episodio, título y URL del video son obligatorios.', 'danger')
        else:
            try:
                numero_episodio = int(numero_episodio)
                duracion_minutos = int(duracion_minutos_str) if duracion_minutos_str else None

                nuevo_episodio = Episodio(
                    numero_episodio=numero_episodio,
                    titulo_episodio=titulo_episodio,
                    descripcion=descripcion,
                    url_video=url_video,
                    duracion_minutos=duracion_minutos,
                    temporada_id=temporada.id
                )
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
        db.create_all() # Crea las tablas si no existen
    app.run(debug=True)