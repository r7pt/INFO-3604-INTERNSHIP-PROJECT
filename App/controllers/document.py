import os
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename


class DocumentController:
    PDF_EXTENSIONS = {"pdf"}
    IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    @classmethod
    def _normalize_extensions(cls, allowed_extensions):
        if allowed_extensions is None:
            return set()
        return {str(ext).lower().lstrip(".") for ext in allowed_extensions}

    @classmethod
    def _get_extension(cls, filename):
        if not filename or "." not in filename:
            return ""
        return filename.rsplit(".", 1)[1].lower()

    @classmethod
    def is_allowed_file(cls, filename, allowed_extensions):
        allowed = cls._normalize_extensions(allowed_extensions)
        ext = cls._get_extension(filename)
        return bool(ext and ext in allowed)

    @classmethod
    def ensure_upload_path(cls, owner_id, category):
        base_dir = os.path.join(current_app.instance_path, "uploads", str(owner_id), category)
        os.makedirs(base_dir, exist_ok=True)
        return base_dir

    @classmethod
    def build_filename(cls, original_filename, category, filename_prefix=None):
        safe_name = secure_filename(original_filename or "")
        if not safe_name:
            raise ValueError("Invalid filename")
        prefix = filename_prefix or category
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{ts}_{safe_name}"

    @classmethod
    def absolute_from_relative(cls, relative_path):
        if not relative_path:
            return None
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.abspath(os.path.join(current_app.root_path, relative_path))

    @classmethod
    def relative_from_absolute(cls, absolute_path):
        relative_path = os.path.relpath(absolute_path, current_app.root_path)
        return relative_path.replace("\\", "/")

    @classmethod
    def save_document(cls, file_storage, owner_id, category, allowed_extensions, filename_prefix=None):
        if file_storage is None:
            raise ValueError("Missing file")

        original_name = file_storage.filename or ""
        if not original_name:
            raise ValueError("Missing filename")

        if not cls.is_allowed_file(original_name, allowed_extensions):
            allowed_list = ", ".join(sorted(cls._normalize_extensions(allowed_extensions)))
            raise ValueError(f"Only {allowed_list} files are allowed")

        final_name = cls.build_filename(original_name, category, filename_prefix=filename_prefix)
        target_dir = cls.ensure_upload_path(owner_id, category)
        absolute_path = os.path.join(target_dir, final_name)

        file_storage.save(absolute_path)

        return cls.relative_from_absolute(absolute_path)

    @classmethod
    def delete_document(cls, relative_path):
        if not relative_path:
            return False

        absolute_path = cls.absolute_from_relative(relative_path)
        if not absolute_path or not os.path.exists(absolute_path):
            return False

        os.remove(absolute_path)
        return True

    @classmethod
    def replace_document(cls, file_storage, owner_id, category, allowed_extensions, old_relative_path=None, filename_prefix=None):
        new_relative_path = cls.save_document(
            file_storage=file_storage,
            owner_id=owner_id,
            category=category,
            allowed_extensions=allowed_extensions,
            filename_prefix=filename_prefix,
        )

        if old_relative_path:
            try:
                cls.delete_document(old_relative_path)
            except Exception:
                pass

        return new_relative_path

    @classmethod
    def save_pdf_document(cls, file_storage, owner_id, category, filename_prefix=None):
        return cls.save_document(
            file_storage=file_storage,
            owner_id=owner_id,
            category=category,
            allowed_extensions=cls.PDF_EXTENSIONS,
            filename_prefix=filename_prefix,
        )

    @classmethod
    def save_image_document(cls, file_storage, owner_id, category, filename_prefix=None):
        return cls.save_document(
            file_storage=file_storage,
            owner_id=owner_id,
            category=category,
            allowed_extensions=cls.IMAGE_EXTENSIONS,
            filename_prefix=filename_prefix,
        )

    @classmethod
    def replace_pdf_document(cls, file_storage, owner_id, category, old_relative_path=None, filename_prefix=None):
        return cls.replace_document(
            file_storage=file_storage,
            owner_id=owner_id,
            category=category,
            allowed_extensions=cls.PDF_EXTENSIONS,
            old_relative_path=old_relative_path,
            filename_prefix=filename_prefix,
        )

    @classmethod
    def replace_image_document(cls, file_storage, owner_id, category, old_relative_path=None, filename_prefix=None):
        return cls.replace_document(
            file_storage=file_storage,
            owner_id=owner_id,
            category=category,
            allowed_extensions=cls.IMAGE_EXTENSIONS,
            old_relative_path=old_relative_path,
            filename_prefix=filename_prefix,
        )

    @classmethod
    def save_student_resume(cls, file_storage, student_id, old_relative_path=None):
        return cls.replace_pdf_document(
            file_storage=file_storage,
            owner_id=student_id,
            category="resume",
            old_relative_path=old_relative_path,
            filename_prefix="resume",
        )

    @classmethod
    def save_student_transcript(cls, file_storage, student_id, old_relative_path=None):
        return cls.replace_pdf_document(
            file_storage=file_storage,
            owner_id=student_id,
            category="transcript",
            old_relative_path=old_relative_path,
            filename_prefix="transcript",
        )

    @classmethod
    def save_student_profile_picture(cls, file_storage, student_id, old_relative_path=None):
        return cls.replace_image_document(
            file_storage=file_storage,
            owner_id=student_id,
            category="profile_picture",
            old_relative_path=old_relative_path,
            filename_prefix="profile_picture",
        )

    @classmethod
    def save_weekly_report(cls, file_storage, student_id, week_number, old_relative_path=None):
        return cls.replace_pdf_document(
            file_storage=file_storage,
            owner_id=student_id,
            category="weekly_reports",
            old_relative_path=old_relative_path,
            filename_prefix=f"week{week_number}",
        )