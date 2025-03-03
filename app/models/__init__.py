# 避免循环导入，不要从app导入db
# 直接导入模型
from .user import User, student_courses
from .course import Course
from .homework import Homework
from .submission import Submission
from .feedback import Feedback