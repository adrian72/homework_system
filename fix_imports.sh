#!/bin/bash
# 脚本：fix_imports.sh

# 在所有API文件中修正导入语句
cd /Users/oliver/Desktop/homework_system

# 修复auth.py
sed -i '' 's/from app\.models import db, User/from app import db\nfrom app.models import User/' app/api/auth.py

# 修复courses.py
sed -i '' 's/from app\.models import db, Course/from app import db\nfrom app.models import Course/' app/api/courses.py
sed -i '' 's/from app\.models import db, Course, User/from app import db\nfrom app.models import Course, User/' app/api/courses.py

# 修复feedback.py
sed -i '' 's/from app\.models import db, Submission/from app import db\nfrom app.models import Submission/' app/api/feedback.py
sed -i '' 's/from app\.models import db, Submission, Feedback/from app import db\nfrom app.models import Submission, Feedback/' app/api/feedback.py

# 修复homeworks.py
sed -i '' 's/from app\.models import db, Homework/from app import db\nfrom app.models import Homework/' app/api/homeworks.py
sed -i '' 's/from app\.models import db, Homework, Course/from app import db\nfrom app.models import Homework, Course/' app/api/homeworks.py

# 修复submissions.py
sed -i '' 's/from app\.models import db, Submission/from app import db\nfrom app.models import Submission/' app/api/submissions.py
sed -i '' 's/from app\.models import db, Submission, Homework/from app import db\nfrom app.models import Submission, Homework/' app/api/submissions.py

# 修复users.py
sed -i '' 's/from app\.models import db, User/from app import db\nfrom app.models import User/' app/api/users.py

# 修复wordpress.py
sed -i '' 's/from app\.models import db, User/from app import db\nfrom app.models import User/' app/api/wordpress.py

echo "所有API文件的导入语句已修复"