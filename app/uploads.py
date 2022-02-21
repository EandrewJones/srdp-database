from flask import current_app, flash, request, redirect
from flask_babel import _
from werkzeug.utils import secure_filename
from datetime import timedelta
import imghdr


def get_key(val, d: dict):
    for key, value in d.items():
        if val in value:
            return key
    return None


def get_extension(filename):
    return filename.rsplit(".", 1)[1].lower()


def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return format if format != "jpeg" else "jpg"


class FileUploader:
    def __init__(self, file_object, username):
        # Get filename, bucket, and stream
        self.file_object = file_object
        self.username = username
        self.filename = secure_filename(file_object.filename)
        self.extension = get_extension(filename=file_object.filename)
        self.content_type = file_object.mimetype
        self.stream = file_object.stream
        self.stream.seek(0, 2)
        self.stream_len = self.stream.tell()
        self.stream.seek(0, 0)
        self.bucket = get_key(val=self.extension, d=current_app.config["BUCKETS"])

    def is_allowed_file(self):
        # Check  extension
        is_allowed_extension = (
            "." in self.filename
            and self.extension in current_app.config["ALLOWED_EXTENSIONS"]
        )
        # Verify images
        if self.bucket == "photo":
            is_valid_image = validate_image(stream=self.stream) == self.extension
        else:
            is_valid_image = True
        # Check size
        is_allowed_size = self.stream_len <= current_app.config["MAX_CONTENT_LENGTH"]

        # Determine status and create error message
        payload = {}
        payload["status"] = is_allowed_extension and is_valid_image and is_allowed_size
        msg = ""
        if not is_allowed_extension:
            msg += "file type not allowed and "
        if not is_valid_image:
            msg += msg + "not a valid image and "
        if not is_allowed_size:
            msg += "file too large "
        msg = msg.strip().capitalize()
        if msg.endswith(" and"):
            msg = msg[:-4]
        msg += "."
        payload["message"] = msg

        return payload

    def upload_file(self):
        try:

            # Set args
            key = "/".join([self.username, self.bucket, self.filename])
            extra_args = {"ContentType": self.content_type}
            params = {
                "Bucket": current_app.config["S3_BUCKET"],
                "Key": key,
            }
            expires_in = int(
                timedelta(days=current_app.config["EXP_LENGTH_DAYS"]).total_seconds()
            )

            # upload file to bucket
            current_app.s3.upload_fileobj(
                Fileobj=self.file_object,
                Bucket=current_app.config["S3_BUCKET"],
                Key=key,
                ExtraArgs=extra_args,
            )

            # Get presigned url
            url = current_app.s3.generate_presigned_url(
                ClientMethod="get_object", Params=params, ExpiresIn=expires_in
            )
            return {
                "message": "Upload successful.",
                "url": url,
                "bucket": self.bucket,
                "type": self.content_type,
            }

        except Exception as e:
            current_app.logger.info(e)
            return {
                "message": "Upload failed.",
                "url": None,
                "bucket": None,
                "type": None,
            }


def extract_file_from_form(form, username):
    # Check for file
    file_object = form.file_object.data

    # Instantiate empty file info
    file_url = file_bucket = file_type = None

    # Extract info if necessary
    if file_object:
        uploader = FileUploader(file_object=file_object, username=username)
        is_allowed_file = uploader.is_allowed_file()
        if is_allowed_file["status"]:
            file_upload = uploader.upload_file()
            file_url = file_upload["url"]
            file_bucket = file_upload["bucket"]
            file_type = file_upload["type"]
            flash(_(file_upload["message"]))
        else:
            flash(_(is_allowed_file["message"]))

    return file_url, file_bucket, file_type
