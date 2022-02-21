from datetime import datetime
from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    g,
    jsonify,
    current_app,
)
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from flask_paginate import Pagination, get_page_args
from guess_language import guess_language
from app import db
from app.main.forms import (
    EditProfileForm,
    EmptyForm,
    PostForm,
    SearchForm,
    MessageForm,
    CommentForm,
    RepostForm,
)
from app.models import User, Post, Message, Notification
from app.translate import translate
from app.main import bp
from app.uploads import extract_file_from_form
import json


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        # Check language
        language = guess_language(form.post.data)
        if language == "UNKNOWN" or len(language) > 5:
            language = ""

        # Extract file
        file_url, file_bucket, file_type = extract_file_from_form(
            form=form, username=current_user.username
        )

        # Create post
        post = Post(
            body=form.post.data,
            author=current_user,
            media_url=file_url,
            media_class=file_bucket,
            media_type=file_type,
            language=language,
        )
        db.session.add(post)
        db.session.commit()
        flash(_("Your post is now live!"))
        return redirect(url_for("main.index"))
    page = request.args.get("page", 1, type=int)
    query = current_user.followed_posts
    pagination = query.order_by(Post.created_at.desc()).paginate(
        page, current_app.config["POSTS_PER_PAGE"], False
    )
    posts = pagination.items
    next_url = (
        url_for("main.index", page=pagination.next_num) if pagination.has_next else None
    )
    prev_url = (
        url_for("main.index", page=pagination.prev_num) if pagination.has_prev else None
    )
    return render_template(
        "index.html",
        title=_("Home"),
        form=form,
        posts=posts,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/explore")
@login_required
def explore():
    page = request.args.get("page", 1, type=int)
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page, current_app.config["POSTS_PER_PAGE"], False
    )
    posts = pagination.items
    next_url = (
        url_for("main.explore", page=pagination.next_num)
        if pagination.has_next
        else None
    )
    prev_url = (
        url_for("main.explore", page=pagination.prev_num)
        if pagination.has_prev
        else None
    )
    return render_template(
        "index.html",
        title=_("Explore"),
        posts=posts,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/user/<string:username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = user.posts.order_by(Post.created_at.desc()).paginate(
        page, current_app.config["POSTS_PER_PAGE"], False
    )
    next_url = (
        url_for("main.user", username=user.username, page=posts.next_num)
        if posts.has_next
        else None
    )
    prev_url = (
        url_for("main.user", username=user.username, page=posts.prev_num)
        if posts.has_prev
        else None
    )
    form = EmptyForm()
    return render_template(
        "user.html",
        user=user,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
        form=form,
    )


@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_("Your changes have been saved."))
        return redirect(url_for("main.user", username=current_user.username))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template(
        "edit_profile.html", title=_("Edit Profile"), form=form, user=current_user
    )


@bp.route("/post/<int:post_id>")
@login_required
def post_thread(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    return render_template("post.html", post=post)


@bp.route("/follows/<int:user_id>/<action>")
@login_required
def follow_action(user_id, action):
    user = User.query.filter_by(id=user_id).first_or_404()
    if action == "follow":
        current_user.follow(user)
        user.add_notification("unread_follow_count", user.new_follows().count())
        db.session.commit()
        flash(_("You are now following %(username)s!", username=user.username))
    if action == "unfollow":
        current_user.unfollow(user)
        db.session.commit()
        flash(_("You are no longer following %(username)s.", username=user.username))
    return redirect(request.referrer)


@bp.route("/like/<int:post_id>/<action>")
@login_required
def like_action(post_id, action):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if action == "like":
        current_user.like_post(post)
        post.author.add_notification(
            "unread_like_count", post.author.new_likes().count()
        )
        db.session.commit()
        flash(_("You liked %(author)s's post.", author=post.author.username))
    if action == "unlike":
        current_user.unlike_post(post)
        db.session.commit()
        flash(_("You unliked %(author)s's post.", author=post.author.username))
    return redirect(request.referrer)


@bp.route("/comment/<int:post_id>", methods=["GET", "POST"])
@login_required
def comment(post_id):
    parent_post = Post.query.filter_by(id=post_id).first_or_404()
    form = CommentForm()
    if form.validate_on_submit():
        # Check language
        language = guess_language(form.comment.data)
        if language == "UNKNOWN" or len(language) > 5:
            language = ""

        # Extract file
        file_url, file_bucket, file_type = extract_file_from_form(
            form=form, username=current_user.username
        )

        # Create comment
        comment = Post(
            body=form.comment.data,
            author=current_user,
            media_url=file_url,
            media_class=file_bucket,
            media_type=file_type,
            is_comment=True,
            language=language,
        )
        parent_post.comment_on_post(comment=comment)
        parent_post.author.add_notification(
            "unread_comment_count", parent_post.author.new_comments().count()
        )
        db.session.commit()
        flash(_("Your comment is now live!"))
        return jsonify(status="ok")
    elif request.method == "GET":
        return render_template("_form_comment.html", form=form, parent_post=parent_post)
    else:
        data = json.dumps(form.errors, ensure_ascii=False)
        return jsonify(data)
    return render_template("_form_comment.html", form=form, parent_post=parent_post)


@bp.route("/repost/<int:post_id>", methods=["GET", "POST"])
@login_required
def repost(post_id):
    root_post = Post.query.filter_by(id=post_id).first_or_404()
    form = RepostForm()
    if form.validate_on_submit():
        # Check language
        language = guess_language(form.comment.data)
        if language == "UNKNOWN" or len(language) > 5:
            language = ""

        # Extract file
        file_url, file_bucket, file_type = extract_file_from_form(
            form=form, username=current_user.username
        )

        # Create comment
        repost = Post(
            body=form.comment.data,
            author=current_user,
            media_url=file_url,
            media_class=file_bucket,
            media_type=file_type,
            is_repost=True,
            language=language,
        )
        root_post.repost_post(repost=repost)
        root_post.author.add_notification(
            "unread_repost_count", root_post.author.new_reposts().count()
        )
        db.session.commit()
        flash(_("Your repost is now live!"))
        return jsonify(status="ok")
    elif request.method == "GET":
        return render_template("_form_repost.html", form=form, parent_post=root_post)
    else:
        data = json.dumps(form.errors, ensure_ascii=False)
        return jsonify(data)
    return render_template("_form_repost.html", form=form, parent_post=root_post)


@bp.route("/translate", methods=["POST"])
@login_required
def translate_text():
    return jsonify(
        {
            "text": translate(
                request.form["text"],
                request.form["source_language"],
                request.form["dest_language"],
            )
        }
    )


@bp.route("/search", methods=["GET"])
@login_required
def search():
    # Main Explore
    if not g.search_form.validate():
        return redirect(url_for("main.explore"))

    # If search query sent, collect results
    # Parameters
    model = request.args.get("model", "post", type=str)
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["POSTS_PER_PAGE"]
    offset = (page - 1) * per_page

    # Results
    payload = {"users": [], "posts": []}
    if model == "post":
        posts, total = Post.search(g.search_form.q.data, page, per_page)
        payload["posts"] = posts
    else:
        users, total = User.search(g.search_form.q.data, page, per_page)
        payload["users"] = users

    # Pagination
    pagination = Pagination(
        page=page, per_page=per_page, total=total, css_framework="bootstrap4"
    )
    next_url = (
        url_for("main.search", q=g.search_form.q.data, page=page + 1)
        if pagination.has_next
        else None
    )
    prev_url = (
        url_for("main.search", q=g.search_form.q.data, page=page - 1)
        if pagination.has_prev
        else None
    )
    if total == 0:
        flash(_("No results found."))
    return render_template(
        "search.html",
        title=_("Search Results"),
        payload=payload,
        model=model,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/send_message/<string:recipient>", methods=["GET", "POST"])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(msg)
        user.add_notification("unread_message_count", user.new_messages())
        db.session.commit()
        flash(_("Your message has been sent."))
        return redirect(url_for("main.user", username=recipient))
    return render_template(
        "send_message.html", title=_("Send Message"), form=form, recipient=recipient
    )


@bp.route("/convo_messages/<string:recipient>", methods=["GET", "POST"])
@login_required
def convo_messages(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(msg)
        user.add_notification("unread_message_count", user.new_messages())
        db.session.commit()
        flash(_("Your message has been sent."))
        return redirect(url_for("main.user", username=recipient))
    return render_template(
        "convo_messages.html", title=_("Send Message"), form=form, recipient=recipient
    )


@bp.route("/messages")
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification("unread_message_count", 0)
    db.session.commit()
    page = request.args.get("page", 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()
    ).paginate(page, current_app.config["POSTS_PER_PAGE"], False)
    next_url = (
        url_for("main.messages", page=messages.next_num) if messages.has_next else None
    )
    prev_url = (
        url_for("main.messages", page=messages.prev_num) if messages.has_prev else None
    )
    return render_template(
        "messages.html", messages=messages.items, next_url=next_url, prev_url=prev_url
    )


@bp.route("/updates")
@login_required
def updates():
    # Query updates
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["POSTS_PER_PAGE"]
    offset = (page - 1) * per_page
    updates, total = current_user.updates(offset=offset, per_page=per_page)
    pagination = Pagination(
        page=page, per_page=per_page, total=total, css_framework="bootstrap4"
    )
    next_url = url_for("main.updates", page=page + 1) if pagination.has_next else None
    prev_url = url_for("main.updates", page=page - 1) if pagination.has_prev else None

    # Clear notifications
    # TODO: clears all notifcaitons even though only first 'per_page' sender_id
    # fix
    current_user.last_updates_read_time = datetime.utcnow()
    update_names = [
        "unread_like_count",
        "unread_comment_count",
        "unread_follow_count",
        "unread_repost_count",
    ]
    for name in update_names:
        current_user.add_notification(name, 0)
    db.session.commit()

    return render_template(
        "updates.html",
        updates=updates,
        title=_("Activity"),
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/export_posts")
@login_required
def export_posts():
    if current_user.get_task_in_progress("export_posts"):
        flash(_("An export task is currently in progress"))
    else:
        current_user.launch_task("export_posts", _("Exporting posts..."))
        db.session.commit()
    return redirect(url_for("main.user", username=current_user.username))


@bp.route("/notifications")
@login_required
def notifications():
    since = request.args.get("since", 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since
    ).order_by(Notification.timestamp.asc())
    return jsonify(
        [
            {"name": n.name, "data": n.get_data(), "timestamp": n.timestamp}
            for n in notifications
        ]
    )
