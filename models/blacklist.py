from extensions import db
from datetime import datetime
import uuid

class BlacklistEntry(db.Model):
    __tablename__ = "blacklist_entries"

    id             = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email          = db.Column(db.String(255), nullable=False, unique=True, index=True)
    app_uuid       = db.Column(db.String(36),  nullable=False)
    blocked_reason = db.Column(db.String(255), nullable=True)
    request_ip     = db.Column(db.String(45),  nullable=False)   # IPv4 o IPv6
    created_at     = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<BlacklistEntry {self.email}>"
