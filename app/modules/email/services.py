from flask_mail import Mail, Message
from flask import current_app, url_for
from app import db
from app.modules.dataset.models import DataSet
from app.modules.auth.models import User
from app.modules.profile.models import UserFollowUser
from app.modules.community.models import CommunityUser, CommunityFollower, Community


def send_email(recipient, subject, body):
    try:
        msg = Message(subject=subject, recipients=[recipient], body=body)
        mail = Mail()
        mail.send(msg)
        current_app.logger.info(f"Correo enviado a {recipient}")
    except Exception as e:
        current_app.logger.error(f"Error enviando correo a {recipient}: {e}")


def build_author_email_body(user, dataset, url):
    return f"""
    Hola,

    {user.profile.name} {user.profile.surname} ha publicado un nuevo dataset en ComponentesHub:

    Título: {dataset.ds_meta_data.title}
    Descripción: {dataset.ds_meta_data.description}
    Tipo de publicación: {dataset.get_cleaned_publication_type()}
    DOI: {dataset.ds_meta_data.dataset_doi}
    
    Enlace: {url}
    
    Visita ComponentesHub para más información.

    Saludos,
    El equipo de ComponentesHub
    """


def build_community_email_body(community, dataset, url):
    return f"""
    Hola,

    La comunidad "{community.name}" tiene un nuevo dataset publicado por uno de sus miembros:

    Título: {dataset.ds_meta_data.title}
    Descripción: {dataset.ds_meta_data.description}
    Tipo de publicación: {dataset.get_cleaned_publication_type()}
    DOI: {dataset.ds_meta_data.dataset_doi}

    Enlace: {url}
    
    ¡Gracias por seguir la comunidad!
    
    Visita ComponentesHub para más información.

    Saludos,
    El equipo de ComponentesHub
    """


def notify_followers_new_dataset(dataset: DataSet):

    # Validar DOI
    if not dataset.ds_meta_data.dataset_doi:
        current_app.logger.warning(
            f"Dataset {dataset.id} no tiene DOI. No se enviará notificación."
        )
        return

    # Obtener usuario autor del dataset
    user = db.session.query(User).get(dataset.user_id)
    if not user:
        current_app.logger.warning(
            f"Usuario {dataset.user_id} no existe. No se enviará notificación."
        )
        return

    # URL del dataset
    url = (
        dataset.get_componenteshub_doi()
        or url_for("dataset.download_dataset", dataset_id=dataset.id, _external=True)
    )

    # Notificar a los seguidores del autor
    author_followers = [
        uf.follower for uf in user.user_followers if uf.follower.email
    ]

    notified_user_ids = set()

    if author_followers:
        subject = f"Nuevo dataset publicado: {dataset.ds_meta_data.title}"
        body = build_author_email_body(user, dataset, url)

        for follower in author_followers:
            send_email(follower.email, subject, body)
            notified_user_ids.add(follower.id)

    # Notificar a los seguidores de las comunidades del autor
    user_communities = CommunityUser.query.filter_by(user_id=user.id).all()

    for cu in user_communities:

        community = Community.query.get(cu.community_id)
        if not community:
            continue

        community_follower_links = CommunityFollower.query.filter_by(
            community_id=community.id
        ).all()

        community_followers = [
            db.session.query(User).get(cf.user_id)
            for cf in community_follower_links
        ]

        # Filtrar usuarios válidos y que no hayan sido notificados ya
        filtered_followers = [
            u for u in community_followers
            if u and u.email and u.id not in notified_user_ids
        ]

        if not filtered_followers:
            continue

        subject = f"Nuevo dataset en la comunidad {community.name}"
        body = build_community_email_body(community, dataset, url)

        for follower in filtered_followers:
            send_email(follower.email, subject, body)
            notified_user_ids.add(follower.id)
