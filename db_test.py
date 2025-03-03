#!/usr/bin/env python
import os
import sqlite3
from pathlib import Path

# 打印当前工作目录
print(f"当前工作目录: {os.getcwd()}")

# 定义数据库文件的绝对路径
db_dir = os.path.join(os.getcwd(), 'instance')
db_file = os.path.join(db_dir, 'dev.sqlite')

print(f"数据库目录: {db_dir}")
print(f"数据库文件路径: {db_file}")

# 检查目录是否存在
if not os.path.exists(db_dir):
    print(f"创建目录: {db_dir}")
    os.makedirs(db_dir, exist_ok=True)

# 检查权限
print(f"目录权限: {oct(os.stat(db_dir).st_mode)[-3:]}")
if os.path.exists(db_file):
    print(f"文件权限: {oct(os.stat(db_file).st_mode)[-3:]}")

# 测试是否可以直接使用sqlite3连接
try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)')
    cursor.execute('INSERT INTO test (name) VALUES (?)', ('test_item',))
    conn.commit()
    print("SQLite直接连接测试: 成功!")
    
    # 检索数据
    cursor.execute('SELECT * FROM test')
    print(f"测试数据: {cursor.fetchall()}")
    
    conn.close()
except Exception as e:
    print(f"SQLite直接连接测试: 失败! 错误: {str(e)}")

print("\n现在将使用绝对路径更新config.py...")

# 更新配置文件使用绝对路径
config_path = os.path.join(os.getcwd(), 'config.py')
with open(config_path, 'r') as f:
    config_content = f.read()

# 替换开发配置中的数据库路径
absolute_db_path = f"sqlite:///{db_file}"
updated_content = config_content.replace(
    "SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/dev.sqlite'", 
    f"SQLALCHEMY_DATABASE_URI = '{absolute_db_path}'"
)

with open(config_path, 'w') as f:
    f.write(updated_content)

print(f"配置已更新，使用绝对路径: {absolute_db_path}")
print("\n请重启Flask应用并再次尝试！")
