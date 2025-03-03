#!/usr/bin/env python
import re

# 读取文件
with open('app/__init__.py', 'r') as f:
    content = f.read()

# 检查是否已有上下文处理器
if 'app.context_processor' not in content:
    # 添加上下文处理器
    create_app_function = re.search(r'def create_app\([^)]*\):.*?return app', content, re.DOTALL).group(0)
    
    # 在返回app前添加上下文处理器
    modified_function = create_app_function.replace(
        'return app',
        '''
    # 添加上下文处理器
    @app.context_processor
    def inject_globals():
        """注入全局变量到模板中"""
        from datetime import datetime
        return {
            'now': datetime.now()
        }
    
    return app''')
    
    # 替换原始函数
    modified_content = content.replace(create_app_function, modified_function)
    
    # 写回文件
    with open('app/__init__.py', 'w') as f:
        f.write(modified_content)
    
    print("已添加上下文处理器到app/__init__.py")
else:
    print("上下文处理器已存在，无需修改")
