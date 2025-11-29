from flask import jsonify, make_response, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.modules.community import community_bp
from app.modules.community.services import CommunityService, CommunityUserService
from app.modules.community.forms import CreateCommunityForm, FindCommunityForm
from app.modules.profile.models import UserProfile
from app.modules.dataset.models import DataSet
from app.modules.community.models import Community

from app import db

community_service = CommunityService()
community_user_service = CommunityUserService()

base_url = "/community"


@community_bp.route(base_url, methods=['GET'])
@login_required
def index():
    # Mostrar solo las comunidades del usuario (vista por defecto)
    communities = community_service.get_communities_by_user_id(current_user.id)
    return render_template('community/index.html', communities=communities, show_all=False)


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
    # permitir ver la comunidad aunque no pertenezcas a ella
    community_user = community_user_service.get_by_user_id_and_community(community_id=community.id,
                                                                         user_id=current_user.id)
    is_member = True if community_user else False
    is_admin = community_user.is_admin if community_user else False

    users = {}
    community_users = community_user_service.get_users_by_community(community_id=community.id)
    for cu in community_users:
        user_profile = UserProfile.query.filter_by(user_id=cu.user_id).first()
        if user_profile:
            users[user_profile.name] = 1 if cu.is_admin else 0

    current_user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    current_user_name = current_user_profile.name if current_user_profile else None

    datasets = []
    for cu in community_users:
        datasets += db.session.query(DataSet).filter(
            DataSet.user_id == cu.user_id).order_by(
                DataSet.created_at.desc())

    return render_template('community/show.html', community=community,
                           users=users, usersSize=len(community_users),
                           datasets=datasets, datasetsSize=len(datasets),
                           is_admin=is_admin, is_member=is_member,
                           current_user_name=current_user_name)


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
        community = community_service.create(name=name, description=description,
                                             code=code)
        community = community_service.get_community_by_code(code)
        community_user_service.create(user_id=current_user.id, community_id=community.id, is_admin=True)
        return redirect(url_for('community.get_community', community_id=community.id))
    return render_template('community/create.html', createForm=CreateCommunityForm())


@community_bp.route(base_url + "/join", methods=["GET", "POST"])
@login_required
def join_community():
    form = FindCommunityForm()
    if form.validate_on_submit():
        code = form.joinCode.data
        community = community_service.get_community_by_code(code)
        if not community:
            flash("No existe ninguna comunidad con este código", "error")
            return redirect(url_for('community.join_community'))
        community_user = community_user_service.get_by_user_id_and_community(current_user.id, community.id)
        if community_user:
            flash("Ya perteneces a esta comunidad", "error")
            return redirect(url_for('community.join_community'))
        community_user_service.create(user_id=current_user.id, community_id=community.id)
        return redirect(url_for('community.get_community', community_id=community.id))
    return render_template('community/join.html', findForm=FindCommunityForm())


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
