from datetime import datetime
import json
from app import db

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homeworks.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)  # JSON存储文件路径等信息
    comment = db.Column(db.Text, nullable=True)
    version = db.Column(db.Integer, default=1)  # 版本号，支持多次提交
    status = db.Column(db.String(20), default='submitted')  # submitted, graded, needs_revision, revised
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 反馈关系
    feedback = db.relationship('Feedback', backref='submission', lazy='dynamic', cascade='all, delete-orphan')
    
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
            'homework_id': self.homework_id,
            'student_id': self.student_id,
            'content': self.content_data,
            'comment': self.comment,
            'version': self.version,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Submission {self.id} by Student {self.student_id}>'