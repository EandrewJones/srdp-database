from flask import render_template, current_app
from flask_babel import _
from app.email import send_email

# TODO: Replace Cover name with real name
def send_password_reset_email(user):
    token = user.get_reset_password_token()
    cover_name = current_app.config['COVER_NAME']
    send_email(_('[%s] Reset Your Password' % cover_name),
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))
