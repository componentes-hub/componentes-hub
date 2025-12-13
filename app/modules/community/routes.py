from flask import jsonify, make_response, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.modules.community import community_bp
from app.modules.community.services import CommunityService, CommunityUserService
from app.modules.community.forms import CreateCommunityForm
from app.modules.profile.models import UserProfile
from app.modules.dataset.models import DataSet
from app.modules.community.models import Community, CommunityFollower

from app import db

community_service = CommunityService()
community_user_service = CommunityUserService()

base_url = "/community"


@community_bp.route(base_url, methods=['GET'])
@login_required
def index():
    # Comunidades donde es miembro
    member_communities = community_user_service.get_communities_by_user_id(current_user.id)

    # Comunidades que sigue
    followed_communities = community_user_service.get_followed_communities(current_user.id)

    return render_template(
        'community/index.html',
        member_communities=member_communities,
        followed_communities=followed_communities,
        show_all=False
    )


@community_bp.route(base_url + "/all", methods=['GET'])
@login_required
def all_communities():
    # Mostrar todas las comunidades
    communities = Community.query.order_by(Community.name.asc()).all()
    return render_template('community/index.html', communities=communities, show_all=True)


@community_bp.route(base_url + "/<int:community_id>", methods=["GET"])
@login_required
def get_community(community_id):
    community = community_service.get_or_404(id=community_id)
    if not community:
        return make_response(jsonify({"message": "Community not found"}), 404)

    # Ver si el usuario es miembro de la comunidad
    community_user = community_user_service.get_by_user_id_and_community(
        community_id=community.id,
        user_id=current_user.id
    )

    is_member = True if community_user else False
    is_admin = community_user.is_admin if community_user else False

    # Ver si el usuario es seguidor de la comunidad
    follower = None
    if not is_member:
        follower = community_user_service.get_follower(
            user_id=current_user.id,
            community_id=community.id
        )

    is_follower = follower is not None

    # Lista de miembros
    users = {}
    community_users = community_user_service.get_users_by_community(community_id=community.id)
    for cu in community_users:
        user_profile = UserProfile.query.filter_by(user_id=cu.user_id).first()
        if user_profile:
            users[user_profile.name] = 1 if cu.is_admin else 0

    # Perfil del usuario actual
    current_user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    current_user_name = current_user_profile.name if current_user_profile else None

    datasets = []
    for cu in community_users:
        datasets += db.session.query(DataSet).filter(
            DataSet.user_id == cu.user_id
        ).order_by(DataSet.created_at.desc())

    # Lista de seguidores
    followers = (
        CommunityFollower.query
        .filter_by(community_id=community.id)
        .join(UserProfile, UserProfile.user_id == CommunityFollower.user_id)
        .with_entities(UserProfile.name)
        .all()
    )

    followers_list = [f.name for f in followers]
    followers_size = len(followers_list)

    # Render final
    return render_template(
        'community/show.html',
        community=community,
        users=users,
        usersSize=len(community_users),
        followers=followers_list,
        followersSize=followers_size,
        datasets=datasets,
        datasetsSize=len(datasets),
        is_admin=is_admin,
        is_member=is_member,
        is_follower=is_follower,
        current_user_name=current_user_name
    )


@community_bp.route(base_url + "/create", methods=["GET", "POST"])
@login_required
def create_community():
    form = CreateCommunityForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        code = form.code.data
        community = community_service.get_community_by_code(code)
        if community:
            flash("El código ya está en uso", "error")
            return redirect(url_for('community.create_community'))
        community = community_service.create(name=name, description=description, code=code)
        community = community_service.get_community_by_code(code)
        community_user_service.create(user_id=current_user.id, community_id=community.id, is_admin=True)
        return redirect(url_for('community.get_community', community_id=community.id))
    return render_template('community/create.html', createForm=CreateCommunityForm())


@community_bp.route(base_url + "/update/<int:community_id>", methods=["GET", "POST"])
@login_required
def update_community(community_id):
    form = CreateCommunityForm()
    community = community_service.get_by_id(community_id)
    community_user = community_user_service.get_by_user_id_and_community(user_id=current_user.id, 
                                                                         community_id=community_id)
    if not community_user or not community_user.is_admin:
        flash("No tienes permisos para eliminar esta comunidad", "error")
        return redirect(url_for('community.get_community', community_id=community_id))
    if form.validate_on_submit():
        name = form.name.data
        if not name:
            name = community.name
        description = form.description.data
        if not description:
            description = community.description
        code = form.code.data
        if not code:
            code = community.code
        else:
            community = community_service.get_community_by_code(code)
            if community:
                flash("El código ya está en uso", "error")
                return redirect(url_for('community.update_community', community_id=community_id))
        community = community_service.update(community_id, name=name, code=code, description=description)
        if not community:
            return flash("Comunidad no encontrada", "error")
        return redirect(url_for('community.get_community', community_id=community.id))
    return render_template('community/edit.html', form=form, community=community)


@community_bp.route(base_url + "/delete/<int:community_id>", methods=["POST"])
@login_required
def delete_community(community_id):
    community = community_service.get_or_404(community_id)
    if not community:
        return flash("Comunidad no encontrada", "error")

    community_user = community_user_service.get_by_user_id_and_community(user_id=current_user.id, 
                                                                         community_id=community_id)
    if not community_user or not community_user.is_admin:
        flash("No tienes permisos para eliminar esta comunidad", "error")
        return redirect(url_for('community.get_community', community_id=community_id))

    community_users = community_user_service.get_users_by_community(community_id=community_id)
    for community_user in community_users:
        community_user_service.delete(community_user.id)
    community_service.delete(community_id)
    return redirect(url_for('community.index', community_id=community_id))


@community_bp.route(base_url + "/leave/<int:community_id>", methods=["POST"])
@login_required
def leave_community(community_id):
    community_user = community_user_service.get_by_user_id_and_community(user_id=current_user.id,
                                                                         community_id=community_id)
    if not community_user:
        flash("No perteneces a esta comunidad", "error")
        return redirect(url_for('community.index'))

    community_user_service.delete(community_user.id)

    community_users = community_user_service.get_users_by_community(community_id=community_id)
    if len(community_users) == 0:
        community_service.delete(community_id)
    flash("Has abandonado la comunidad exitosamente", "success")
    return index()


@community_bp.route(base_url + "/follow/<int:community_id>", methods=["POST"])
@login_required
def follow_community(community_id):
    # Seguir una comunidad
    community = community_service.get_or_404(community_id)

    follower = community_user_service.get_follower(current_user.id, community_id)
    if follower:
        flash("You already follow this community", "info")
        return redirect(url_for('community.get_community', community_id=community_id))

    community_user_service.create_follower(user_id=current_user.id, community_id=community.id)

    flash("You now follow this community", "success")
    return redirect(url_for('community.get_community', community_id=community_id))


@community_bp.route(base_url + "/unfollow/<int:community_id>", methods=["POST"])
@login_required
def unfollow_community(community_id):
    # Dejar de seguir una comunidad
    follower = community_user_service.get_follower(current_user.id, community_id)
    if not follower:
        flash("You don't follow this community", "error")
        return redirect(url_for('community.get_community', community_id=community_id))

    community_user_service.delete_follower(follower.id)
    flash("You unfollowed the community", "success")
    return redirect(url_for('community.get_community', community_id=community_id))
