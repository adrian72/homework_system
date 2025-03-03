#!/bin/bash
# 脚本：fix_view_imports.sh

cd /Users/oliver/Desktop/homework_system

# 修复auth.py的导入
sed -i '' 's/from app\.models import User, db/from app import db\nfrom app.models import User/' app/views/auth.py

# 修复student.py的导入
sed -i '' 's/from app\.models import Course, Homework, Submission, Feedback, User, db/from app import db\nfrom app.models import Course, Homework, Submission, Feedback, User/' app/views/student.py

# 修复teacher.py的导入
sed -i '' 's/from app\.models import Course, Homework, Submission, Feedback, User, db/from app import db\nfrom app.models import Course, Homework, Submission, Feedback, User/' app/views/teacher.py

# 修复admin.py的导入
sed -i '' 's/from app\.models import User, Course, Homework, Submission, Feedback, db/from app import db\nfrom app.models import User, Course, Homework, Submission, Feedback/' app/views/admin.py