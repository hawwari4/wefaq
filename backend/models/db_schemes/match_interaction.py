from datetime import datetime

from .base import db


class CompatibilityRequest(db.Model):
    """A private compatibility request between two approved candidates."""
    __tablename__ = 'compatibility_requests'
    __table_args__ = (
        db.UniqueConstraint('sender_id', 'receiver_id', name='uq_compatibility_request_pair'),
    )

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])


class SavedCandidate(db.Model):
    """A candidate privately saved by another candidate."""
    __tablename__ = 'saved_candidates'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'candidate_id', name='uq_saved_candidate_pair'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    owner = db.relationship('User', foreign_keys=[user_id])
    candidate = db.relationship('User', foreign_keys=[candidate_id])
