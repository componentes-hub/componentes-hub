from flask_mail import Mail, Message
from flask import current_app, url_for
from app import db
from app.modules.dataset.models import DataSet
from app.modules.auth.models import User
from app.modules.dataset.models import Author
from app.modules.profile.models import UserFollowUser


def send_notification_email(to, title, dataset_name, link):
    msg = Message(
        subject=f"Nueva publicación: {dataset_name}",
        recipients=[to]
    )
    msg.body = f"""
        Hola,

        El autor/usuario/comunidad "{title}" ha publicado un nuevo dataset:

        {dataset_name}

        Puedes verlo aquí:
        {link}

        ¡Un saludo!
    """

    mail = Mail()
    mail.send(msg)

def notify_followers_new_dataset(dataset: DataSet):
   
    # Comprueba que el dataset tenga DOI asignado
    if not dataset.ds_meta_data.dataset_doi:
        current_app.logger.warning(f"Dataset {dataset.id} no tiene DOI. No se enviará notificación.")
        return

    # Obtén el usuario que subió el dataset
    user = db.session.query(User).get(dataset.user_id)
    if not user:
        current_app.logger.warning(f"Usuario {dataset.user_id} no existe. No se enviará notificación.")
        return

    # Obtén los seguidores del usuario
    followers = [uf.follower for uf in user.user_followers if uf.follower.email]

    if not followers:
        current_app.logger.info(f"Usuario {user.id} no tiene seguidores con correo.")
        return

    # Construye el contenido del mensaje
    subject = f"Nuevo dataset publicado: {dataset.ds_meta_data.title}"
    url = dataset.get_componenteshub_doi() or url_for("dataset.download_dataset", dataset_id=dataset.id, _external=True)
    body = f"""
    Hola,

    {user.profile.name} {user.profile.surname} ha publicado un nuevo dataset en ComponentesHub:

    Título: {dataset.ds_meta_data.title}
    Descripción: {dataset.ds_meta_data.description}
    Tipo de publicación: {dataset.get_cleaned_publication_type()}
    Enlace DOI: {dataset.ds_meta_data.dataset_doi}
    Enlace de descarga: {url}
    ¡Visita ComponentesHub para más información!

    Saludos,
    El equipo de ComponentesHub
    """

    # Envía el correo a cada seguidor
    for follower in followers:
        try:
            msg = Message(subject=subject, recipients=[follower.email], body=body)
            mail = Mail()
            mail.send(msg)
            current_app.logger.info(f"Notificación enviada a {follower.email} por el dataset {dataset.id}")
        except Exception as e:
            current_app.logger.error(f"Error enviando correo a {follower.email}: {e}")