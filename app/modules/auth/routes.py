from flask import redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, SignupForm
from app.modules.auth.forms import TwoFactorForm
from app.modules.auth.services import AuthenticationService, SessionDeviceService
from app.modules.profile.services import UserProfileService

from flask import session, send_file, flash
from io import BytesIO

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()
session_device_service = SessionDeviceService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f"Email {email} in use")

        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f"Error creating user: {exc}")

        # Log user
        login_user(user, remember=True)
        session_device_service.create_session(user.id, request)
        return redirect(url_for("public.index"))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        user = authentication_service.repository.get_by_email(form.email.data)
        if user and user.check_password(form.password.data):
            if user.two_factor_enabled and user.totp_secret:
                session["pre_2fa_user_id"] = user.id
                session["pre_2fa_remember_me"] = form.remember_me.data
                return redirect(url_for("auth.two_factor_verify"))
            login_user(user, remember=form.remember_me.data)
            session_device_service.create_session(user.id, request)
            return redirect(url_for("public.index"))
        return render_template("auth/login_form.html", form=form, error="Invalid credentials")
    # Siempre retornar el formulario en GET o si no se cumple el POST
    return render_template("auth/login_form.html", form=form)


@auth_bp.route("/2fa/setup", methods=["GET", "POST"])
def two_factor_setup():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    user = current_user
    form = TwoFactorForm()
    import pyotp
    if not getattr(user, "totp_secret", None):
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.two_factor_enabled = False
        authentication_service.repository.session.add(user)
        authentication_service.repository.session.commit()
    else:
        secret = user.totp_secret
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Componentes Hub")
    return render_template("auth/2fa_setup.html", uri=uri, secret=secret, form=form)


@auth_bp.route("/2fa/qrcode")
def two_factor_qrcode():
    if not current_user.is_authenticated:
        return ("", 401)
    user = current_user
    if not getattr(user, "totp_secret", None):
        return ("No 2FA secret configured", 404)
    import qrcode
    import pyotp
    uri = pyotp.totp.TOTP(user.totp_secret).provisioning_uri(name=user.email, issuer_name="Componentes Hub")
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@auth_bp.route("/2fa/verify", methods=["GET", "POST"])
def two_factor_verify():
    form = TwoFactorForm()
    user_id = session.get("pre_2fa_user_id")
    error = None
    if not user_id:
        return redirect(url_for("auth.login"))
    user = authentication_service.repository.model.query.get(user_id)
    if not user:
        return redirect(url_for("auth.login"))
    if request.method == "POST" and form.validate_on_submit():
        import pyotp
        token = form.token.data.strip()
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(token, valid_window=1):
            remember_me = session.get("pre_2fa_remember_me", False)
            login_user(user, remember=remember_me)
            session_device_service.create_session(user.id, request)
            session.pop("pre_2fa_user_id", None)
            session.pop("pre_2fa_remember_me", None)
            return redirect(url_for("public.index"))
        error = "Código de autenticación inválido."
    return render_template("auth/2fa_verify.html", form=form, error=error)


@auth_bp.route("/2fa/confirm", methods=["POST"])
def two_factor_confirm():
    if not current_user.is_authenticated:
        return ("", 401)
    form = TwoFactorForm()
    import pyotp
    error = None
    if form.validate_on_submit():
        token = form.token.data.strip()
        user = current_user
        totp = pyotp.TOTP(user.totp_secret)
        # Use valid_window=1 to allow tokens from ±30 seconds (current and adjacent windows)
        if totp.verify(token, valid_window=1):
            user.two_factor_enabled = True
            authentication_service.repository.session.add(user)
            authentication_service.repository.session.commit()
            flash("Autenticación en dos pasos activada.", "success")
            return redirect(url_for("profile.edit_profile"))
        error = "Código de autenticación inválido."
    secret = current_user.totp_secret
    uri = pyotp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name="Componentes Hub")
    return render_template("auth/2fa_setup.html", uri=uri, secret=secret, form=form, error=error)


@auth_bp.route("/logout")
def logout():
    session_id = session.get('device_session_id')
    if session_id and current_user.is_authenticated:
        session_device_service.close_session(session_id, current_user.id)
    logout_user()
    return redirect(url_for("public.index"))


@auth_bp.route("/sessions", methods=["GET"])
def show_sessions():
    """Display all active sessions for the current user"""
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    sessions = session_device_service.get_user_sessions(current_user.id)
    current_session = session_device_service.get_current_session(current_user.id)

    # Mark current session
    for sess in sessions:
        sess.is_current = (current_session and sess.id == current_session.id)

    return render_template("auth/sessions.html", sessions=sessions)


@auth_bp.route("/sessions/current", methods=["GET"])
def get_current_session():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    current_session = session_device_service.get_current_session(current_user.id)

    if current_session:
        return jsonify({
            'success': True,
            'session': current_session.to_dict()
        }), 200

    return jsonify({
        'success': False,
        'message': 'No active session'
    }), 404


@auth_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
def close_session(session_id):
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    current_session = session_device_service.get_current_session(current_user.id)
    if current_session and current_session.id == session_id:
        return jsonify({
            'success': False,
            'message': 'Use the logout button to close your current session'
        }), 400

    if session_device_service.close_session(session_id, current_user.id):
        return jsonify({
            'success': True,
            'message': 'Session closed successfully'
        }), 200

    return jsonify({
        'success': False,
        'message': 'Session not found'
    }), 404


@auth_bp.route("/sessions/close-all-others", methods=["POST"])
def close_all_other_sessions():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    count = session_device_service.close_all_other_sessions(current_user.id)

    return jsonify({
        'success': True,
        'message': f'{count} session(s) closed',
        'closed_count': count
    }), 200
