from datetime import datetime
from app import db

class Homework(db.Model):
    __tablename__ = 'homeworks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    assignment_type = db.Column(db.String(20), nullable=False)  # 'essay', 'oral'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 提交关系
    submissions = db.relationship('Submission', backref='homework', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'course_id': self.course_id,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'assignment_type': self.assignment_type,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Homework {self.title}>'