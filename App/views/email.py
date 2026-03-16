import os
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename

from flask_jwt_extended import jwt_required, current_user

from App.database import db
from App.models.email import Email
from App.controllers.email import (
    list_inbox_emails
)

email_views = Blueprint('email_views', __name__, url_prefix='/api/email')

def _json_error(message, status=400, extra=None):
    payload = {'error': message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status

@email_views.get('/inbox')
@jwt_required()
Def get_inbox():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    userid=getattr(current_user, 'id', None)
    inbox = get_all_emails_recieved_by_user(userid)
    return jsonify(inbox)



@email_views.get('/outbox')
@jwt_required ()
Def get_outbox()
    if current_user is None:
        return _json_error('Not authenticated', 401)
    userid = getattr(current_user,'id',None)
    outbox = get_all_emails_sent_by_user(userid)
    return jsonify(outbox)

@email_views.post('/send-email')
@jwt_required()
def api_create_email():
    if current_user is None:
        return _json_error('Not authenticated', 401)
        userid = getattr(current_user,'id',None)

    try:
        sender =getattr(current_user,'email',None)
        recipient_id =request.form.get('recipient_id')
        subject = request.form.get('subject')
        description =request.form.get('description')
        graphic = request.files.get("graphic")
        attachment = request.files.get("attachment")

        email= Email(sender,recipient,subject, description, graphic, attachment)

        db.session.add(email)
        db.session.commit()

        attachment.append(graphic)
        if send_email(to_email=recipient,subject=subject, body_text=description,attachments= attachment):
            flash("email sent")
            return render_template(email.html)#render back updated inbox view with new email
    except exception as e:
        db.session.rollback()
        flash("failed to send email")
        print( "error occurred creating email",e)

@email_views.post('/delete_email')
@jwt_required()
def api_delete_email():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    try:
        userid=getattr(current_user,'id',None
        Email=request.form.get('email')
        db.session.delete(email)
        db.session.commit()
    except db error as e:
        db.session.rollback()
        flash("failed to delete email")
        print( "error occurred deleting email",e)

@email_views.post("/reply-email")
@jwt_required()
def api_reply_email():
     if current_user is None:
        return _json_error('Not authenticated', 401)
    try: 
        email = request.form.get('email')
        description = request.form.get('description')
        attachment = request.files.get('attachment')
        graphic=request.files.get('graphic')
        new_email = reply_email(email.id,description,attachment,graphic)
        db.session.add(email)
        db.session.commit()
        if email:
             if send_email(email.recipient_id,email.subject,body_text = email.description,attachment=email.attachment)
                flash("email sent")
                return render_template(email.html)#render back updated inbox view with new email
    except Exception as e:
        db.session.rollback()
        flash("error occurred while sending email")
        print("the following error occured while replying email ", e)

@email_views.post("/search-email")
@jwt_required()
def api_search_email():
     if current_user is None:
        return _json_error('Not authenticated', 401)
    try: 
        keyword = request.form.get('keyword')
        results, word_count = search_email_header(keyword)
        flash(word_count," occurrences of ",keyword)
        return jsonify(results)
    except Exception as e:
        flash("error occurred while search email")
        print("the following error occured while searching email ", e)

