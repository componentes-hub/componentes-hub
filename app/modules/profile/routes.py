from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService
from app.modules.community.services import CommunityUserService
from app.modules.dataset.models import DataSet, Author, DSMetaData
from flask import flash, render_template, redirect, url_for, request
from flask_login import AnonymousUserMixin, login_required, current_user
from app import db
from app.modules.profile import profile_bp
from app.modules.profile.forms import UserProfileForm
from app.modules.profile.services import UserProfileService
from app.modules.profile.models import UserFollowAuthor, UserFollowUser, UserProfile


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    auth_service = AuthenticationService()
    profile = auth_service.get_authenticated_user_profile
    if not profile:
        return redirect(url_for("public.index"))

    form = UserProfileForm()
    if request.method == "POST":
        service = UserProfileService()
        result, errors = service.update_profile(profile.id, form)
        return service.handle_service_response(
            result, errors, "profile.edit_profile", "Profile updated successfully", "profile/edit.html", form
        )

    return render_template("profile/edit.html", form=form)

@profile_bp.route('/profile/summary')
@login_required
def my_profile():
    page = request.args.get('page', 1, type=int)
    per_page = 5

    user_datasets_pagination = db.session.query(DataSet) \
        .filter(DataSet.user_id == current_user.id) \
        .order_by(DataSet.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    total_datasets_count = db.session.query(DataSet) \
        .filter(DataSet.user_id == current_user.id) \
        .count()

    # Obtener las filas de seguimiento para mostrar seguidos en el perfil
    followed_authors_rows = UserFollowAuthor.query.filter_by(user_id=current_user.id).all()
    followed_authors = [f.author for f in followed_authors_rows]
    following_users_rows = UserFollowUser.query.filter_by(follower_id=current_user.id).all()
    following_users = [f.followed for f in following_users_rows]
    followed_communities = community_user_service.get_followed_communities(current_user.id)

    return render_template(
        'profile/summary.html',
        user_profile=current_user.profile,
        user=current_user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
        followed_authors=followed_authors,
        following_users=following_users,
        followed_communities=followed_communities
    )

@profile_bp.route('/author/<int:author_id>/projects')
def proyectos_autor(author_id):
    author = Author.query.get(author_id)

    if not author:
        return "Author not found", 404

    datasets = DataSet.query.join(DSMetaData).filter(
        DSMetaData.authors.any(id=author_id)
    ).all()

    return render_template(
        'profile/author_projects.html',
        author=author,
        datasets=datasets
    )

@profile_bp.route('/user/<int:user_id>/projects', methods=['GET'])
def proyectos_usuario(user_id):
    # Si el usuario está logueado y es él mismo, redirige al perfil
    if isinstance(current_user, AnonymousUserMixin) is False and current_user.id == user_id:
        return redirect(url_for('profile.my_profile'))

    # Buscar el usuario en la tabla User
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    profile = user.profile  # relación con UserProfile

    # Datasets del usuario
    datasets = list(DataSet.query.filter(DataSet.user_id == user.id))

    # Seguidores y siguiendo
    followers_rows = UserFollowUser.query.filter_by(followed_id=user.id).all()
    followers_count = len(followers_rows)

    following_rows = UserFollowUser.query.filter_by(follower_id=user.id).all()
    following_users = [f.followed for f in following_rows]

    return render_template(
        'profile/user_projects.html',
        user=user,
        profile=profile,
        datasets=datasets,
        followers_count=followers_count,
        following_users=following_users
    )

community_user_service = CommunityUserService()
    
@profile_bp.route('/user/<int:user_id>/followed_communities')
@login_required
def user_followed_communities(user_id):
    # Redirige a tu propio perfil si es el usuario logueado
    if current_user.id == user_id:
        return redirect(url_for('profile.my_profile'))

    # Obtener el usuario
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    # Obtener las comunidades que sigue
    followed_communities = community_user_service.get_followed_communities(user.id)

    return render_template(
        'profile/user_followed_communities.html',
        user=user,
        followed_communities=followed_communities
    )

@profile_bp.route('/author/<int:author_id>/follow', methods=['POST'])
@login_required
def follow_author(author_id):
    author = Author.query.get(author_id)
    if not author:
        return "Author not found", 404

    existing = UserFollowAuthor.query.filter_by(author_id=author.id, user_id=current_user.id).first()
    if existing:
        flash("You are already following this author", "info")
        return redirect(url_for('profile.proyectos_autor', author_id=author.id))

    follow = UserFollowAuthor(author_id=author.id, user_id=current_user.id)
    db.session.add(follow)
    db.session.commit()
    flash("You are now following this author", "success")
    return redirect(url_for('profile.proyectos_autor', author_id=author.id))  # <-- redirige a autor


@profile_bp.route('/author/<int:author_id>/unfollow', methods=['POST'])
@login_required
def unfollow_author(author_id):
    author = Author.query.get(author_id)
    if not author:
        return "Author not found", 404

    follow = UserFollowAuthor.query.filter_by(author_id=author.id, user_id=current_user.id).first()
    if not follow:
        flash("You are not following this author", "error")
        return redirect(url_for('profile.proyectos_autor', author_id=author.id))

    db.session.delete(follow)
    db.session.commit()
    flash("You have unfollowed this author", "success")
    return redirect(url_for('profile.proyectos_autor', author_id=author.id))  # <-- redirige a autor


@profile_bp.route('/user/<int:user_id>/follow', methods=['POST'])
@login_required
def follow_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    existing = UserFollowUser.query.filter_by(follower_id=current_user.id, followed_id=user.id).first()
    if existing:
        flash("You already follow this user", "info")
        return redirect(url_for('profile.proyectos_usuario', user_id=user.id))

    follow = UserFollowUser(follower_id=current_user.id, followed_id=user.id)
    db.session.add(follow)
    db.session.commit()
    flash("You have followed the user", "success")
    return redirect(url_for('profile.proyectos_usuario', user_id=user.id))


@profile_bp.route('/user/<int:user_id>/unfollow', methods=['POST'])
@login_required
def unfollow_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    follow = UserFollowUser.query.filter_by(follower_id=current_user.id, followed_id=user.id).first()
    if not follow:
        flash("You are not following this user", "error")
        return redirect(url_for('profile.proyectos_usuario', user_id=user.id))

    db.session.delete(follow)
    db.session.commit()
    flash("You have unfollowed the user", "success")
    return redirect(url_for('profile.proyectos_usuario', user_id=user.id))

