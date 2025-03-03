from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin # type: ignore
from datetime import datetime
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='student')  # student, teacher, admin
    wp_user_id = db.Column(db.Integer, nullable=True)  # WordPress用户ID
    avatar_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 课程关系
    courses_as_student = db.relationship('Course', secondary='student_courses', backref=db.backref('students', lazy='dynamic'))
    courses_as_teacher = db.relationship('Course', backref='teacher')
    
    # 作业关系
    submissions = db.relationship('Submission', backref='student', lazy='dynamic')
    feedbacks = db.relationship('Feedback', backref='teacher', lazy='dynamic')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_student(self):
        return self.role == 'student'
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_admin(self):
        return self.role == 'admin'
        
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


# 学生-课程多对多关系表
student_courses = db.Table('student_courses',
    db.Column('student_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))