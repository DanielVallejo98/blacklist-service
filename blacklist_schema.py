from extensions import ma
from models.blacklist import BlacklistEntry
from marshmallow import fields, validate, validates, ValidationError
import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class BlacklistEntrySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model           = BlacklistEntry
        load_instance   = True
        exclude         = ("request_ip",)

    email = fields.Email(required=True)
    app_uuid = fields.Str(
        required=True,
        validate=validate.Regexp(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            flags=re.IGNORECASE,
            error="app_uuid must be a valid UUID."
        )
    )
    blocked_reason = fields.Str(
        load_default=None,
        validate=validate.Length(max=255)
    )

class BlacklistResponseSchema(ma.Schema):
    is_blacklisted = fields.Bool()
    email          = fields.Str()
    blocked_reason = fields.Str(allow_none=True)
    app_uuid       = fields.Str()
    created_at     = fields.DateTime()
