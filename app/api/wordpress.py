# app/api/wordpress.py
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import User
from app.utils.auth import token_required, admin_required
from app.utils.wordpress_client import (
    check_wp_credentials, get_wp_users, get_wp_user, create_wp_post
)

wordpress = Blueprint('wordpress', __name__)

@wordpress.route('/users', methods=['GET'])
@admin_required
def get_wordpress_users(current_user):
    """获取WordPress用户列表（仅限管理员）"""
    users = get_wp_users()
    
    if users is None:
        return jsonify({'message': 'WordPress API请求失败'}), 500
    
    return jsonify({
        'wordpress_users': users
    }), 200


@wordpress.route('/sync-users', methods=['POST'])
@admin_required
def sync_wordpress_users(current_user):
    """同步WordPress用户（仅限管理员）"""
    # 获取WordPress用户
    wp_users = get_wp_users()
    
    if wp_users is None:
        return jsonify({'message': 'WordPress API请求失败'}), 500
    
    # 同步结果
    created = []
    updated = []
    failed = []
    
    for wp_user in wp_users:
        wp_id = wp_user.get('id')
        
        # 查找是否已存在
        user = User.query.filter_by(wp_user_id=wp_id).first()
        
        if user:
            # 更新现有用户
            try:
                user.username = f"wp_{wp_user.get('username')}"
                user.email = wp_user.get('email', f"wp_{wp_user.get('username')}@example.com")
                user.avatar_url = wp_user.get('avatar_url')
                
                db.session.commit()
                updated.append(wp_user.get('username'))
            except Exception as e:
                failed.append({
                    'username': wp_user.get('username'),
                    'error': str(e)
                })
        else:
            # 创建新用户
            try:
                username = f"wp_{wp_user.get('username')}"
                email = wp_user.get('email', f"{username}@example.com")
                
                # 确保用户名唯一
                base_username = username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                # 创建用户
                new_user = User(
                    username=username,
                    email=email,
                    role='student',
                    wp_user_id=wp_id,
                    avatar_url=wp_user.get('avatar_url')
                )
                
                # 设置随机密码（用户需要通过WordPress登录）
                import secrets
                new_user.password = secrets.token_urlsafe(12)
                
                db.session.add(new_user)
                db.session.commit()
                created.append(wp_user.get('username'))
            except Exception as e:
                failed.append({
                    'username': wp_user.get('username'),
                    'error': str(e)
                })
    
    return jsonify({
        'message': 'WordPress用户同步完成',
        'created': created,
        'updated': updated,
        'failed': failed
    }), 200


@wordpress.route('/link-account', methods=['POST'])
@token_required
def link_wordpress_account(current_user):
    """链接WordPress账户"""
    data = request.get_json()
    wp_username = data.get('wp_username')
    wp_password = data.get('wp_password')
    
    if not wp_username or not wp_password:
        return jsonify({'message': 'WordPress用户名和密码都是必填项'}), 400
    
    # 验证WordPress凭据
    wp_user = check_wp_credentials(wp_username, wp_password)
    if not wp_user:
        return jsonify({'message': 'WordPress凭据验证失败'}), 401
    
    # 检查WordPress ID是否已被其他用户关联
    existing_user = User.query.filter_by(wp_user_id=wp_user['id']).first()
    if existing_user and existing_user.id != current_user.id:
        return jsonify({'message': '此WordPress账户已关联到其他用户'}), 400
    
    # 更新用户
    current_user.wp_user_id = wp_user['id']
    current_user.avatar_url = wp_user.get('avatar_url', current_user.avatar_url)
    
    db.session.commit()
    
    return jsonify({
        'message': 'WordPress账户关联成功',
        'wp_user': wp_user
    }), 200


@wordpress.route('/unlink-account', methods=['POST'])
@token_required
def unlink_wordpress_account(current_user):
    """解除WordPress账户关联"""
    if not current_user.wp_user_id:
        return jsonify({'message': '未关联WordPress账户'}), 400
    
    current_user.wp_user_id = None
    db.session.commit()
    
    return jsonify({
        'message': 'WordPress账户解除关联成功'
    }), 200


@wordpress.route('/publish-assignment', methods=['POST'])
@token_required
def publish_assignment_to_wordpress(current_user):
    """将作业发布到WordPress"""
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    status = data.get('status', 'draft')  # 默认为草稿
    
    if not title or not content:
        return jsonify({'message': '标题和内容为必填项'}), 400
    
    # 检查WordPress关联
    if not current_user.wp_user_id:
        return jsonify({'message': '未关联WordPress账户'}), 400
    
    # 发布文章
    result = create_wp_post(title, content, status)
    
    if not result:
        return jsonify({'message': 'WordPress发布失败'}), 500
    
    return jsonify({
        'message': 'WordPress发布成功',
        'post': result
    }), 201


@wordpress.route('/status', methods=['GET'])
@token_required
def check_wordpress_status(current_user):
    """检查WordPress API状态"""
    try:
        # 尝试获取WordPress用户
        wp_user = None
        if current_user.wp_user_id:
            wp_user = get_wp_user(current_user.wp_user_id)
        
        # 检查API配置
        api_url = current_app.config['WP_API_URL']
        api_user = current_app.config['WP_API_USER']
        api_password = current_app.config['WP_API_PASSWORD']
        
        is_configured = bool(api_url and api_user and api_password)
        
        return jsonify({
            'status': 'connected' if is_configured else 'not_configured',
            'wp_api_url': api_url,
            'current_user_linked': bool(current_user.wp_user_id),
            'wp_user': wp_user
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
