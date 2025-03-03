from datetime import datetime
import json
from app import db

class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Float, nullable=True)
    comments = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)  # JSON存储反馈内容，包括图片、音频等
    requires_revision = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def content_data(self):
        if self.content:
            return json.loads(self.content)
        return {}
    
    @content_data.setter
    def content_data(self, data):
        self.content = json.dumps(data)
    
    def to_dict(self):
        return {
            'id': self.id,
            'submission_id': self.submission_id,
            'teacher_id': self.teacher_id,
            'score': self.score,
            'comments': self.comments,
            'content': self.content_data,
            'requires_revision': self.requires_revision,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Feedback {self.id} for Submission {self.submission_id}>'