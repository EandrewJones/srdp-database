import json
import sys
import time
from flask import render_template
from rq import get_current_job
from app import create_app, db
from app.models import User, Post, Task
from app.email import send_email


app = create_app()
app.app_context().push()


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta["progress"] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification(
            "task_progress", {"task_id": job.get_id(), "progress": progress}
        )
        if progress >= 100:
            task.complete = True
        db.session.commit()


def export_posts(user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = user.posts.count()
        for post in user.posts.order_by(Post.created_at.asc()):
            data.append(
                {
                    "body": post.body,
                    "created_at": post.created_at.isoformat() + "Z",
                    "modified_at": post.modified_at.isoformat() + "Z",
                    "likes": post.likes.count(),
                }
            )
            time.sleep(2)
            i += 1
            _set_task_progress(100 * i // total_posts)

        send_email(
            "[%s] Your blog posts" % app.config["COVER_NAME"],
            sender=app.config["ADMINS"][0],
            recipients=[user.email],
            text_body=render_template("email/export_posts.txt", user=user),
            html_body=render_template("email/export_posts.html", user=user),
            attachments=[
                (
                    "posts.json",
                    "application/json",
                    json.dumps({"posts": data}, indent=4),
                )
            ],
            sync=True,
        )
    except:
        _set_task_progress(100)
        app.logger.error("Unhandled exception", exc_info=sys.exc_info())
