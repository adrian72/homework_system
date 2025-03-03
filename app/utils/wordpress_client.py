# app/utils/wordpress_client.py
import requests
import base64
from flask import current_app
import json
import logging
from requests.exceptions import RequestException, Timeout, ConnectionError

# 请求超时设置（秒）
REQUEST_TIMEOUT = 10

def get_wp_api_headers(username=None, password=None):
    """获取WordPress API的认证头
    
    Args:
        username: WordPress用户名，默认为配置中的用户名
        password: WordPress密码，默认为配置中的密码
        
    Returns:
        dict: 包含认证头的字典
        
    Raises:
        ValueError: 如果WordPress API凭据未配置
    """
    username = username or current_app.config.get('WP_API_USER')
    password = password or current_app.config.get('WP_API_PASSWORD')
    
    if not username or not password:
        current_app.logger.error("WordPress API凭据未配置")
        raise ValueError("WordPress API凭据未配置")
    
    # 使用HTTP基本认证
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    return {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/json'
    }

def check_wp_credentials(username, password):
    """验证WordPress用户凭据
    
    Args:
        username: WordPress用户名
        password: WordPress密码
        
    Returns:
        dict: 成功时返回用户信息，失败时返回None
    """
    try:
        # 构建API URL
        api_url = current_app.config.get('WP_API_URL')
        if not api_url:
            current_app.logger.warning("WordPress API URL未配置")
            return None
        
        # 获取认证头
        headers = get_wp_api_headers(username, password)
        
        # 向WordPress API发送请求
        response = requests.get(
            f"{api_url}/wp/v2/users/me", 
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            # 认证成功，返回用户信息
            user_data = response.json()
            return {
                'id': user_data.get('id'),
                'username': user_data.get('slug'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'avatar_url': user_data.get('avatar_urls', {}).get('96', None)
            }
        
        current_app.logger.warning(f"WordPress认证失败: {response.status_code}")
        return None
    except ConnectionError:
        current_app.logger.error("WordPress API连接错误")
        return None
    except Timeout:
        current_app.logger.error("WordPress API请求超时")
        return None
    except Exception as e:
        current_app.logger.error(f"WordPress API请求失败: {str(e)}")
        return None

def get_wp_users():
    """获取WordPress用户列表
    
    Returns:
        list: 用户列表，出错时返回空列表
    """
    try:
        # 构建API URL
        api_url = current_app.config.get('WP_API_URL')
        if not api_url:
            current_app.logger.warning("WordPress API URL未配置")
            return []
        
        # 获取认证头
        try:
            headers = get_wp_api_headers()
        except ValueError:
            return []
        
        # 向WordPress API发送请求
        response = requests.get(
            f"{api_url}/wp/v2/users", 
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            # 返回用户列表
            users = response.json()
            return [{
                'id': user.get('id'),
                'username': user.get('slug'),
                'email': user.get('email'),
                'name': user.get('name'),
                'avatar_url': user.get('avatar_urls', {}).get('96', None)
            } for user in users]
        
        current_app.logger.warning(f"获取WordPress用户失败: {response.status_code}")
        return []
    except Exception as e:
        current_app.logger.error(f"WordPress API请求失败: {str(e)}")
        return []

def get_wp_user(user_id):
    """获取WordPress用户信息
    
    Args:
        user_id: WordPress用户ID
        
    Returns:
        dict: 用户信息，出错时返回None
    """
    try:
        # 构建API URL
        api_url = current_app.config.get('WP_API_URL')
        if not api_url:
            current_app.logger.warning("WordPress API URL未配置")
            return None
        
        # 获取认证头
        try:
            headers = get_wp_api_headers()
        except ValueError:
            return None
        
        # 向WordPress API发送请求
        response = requests.get(
            f"{api_url}/wp/v2/users/{user_id}", 
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            # 返回用户信息
            user_data = response.json()
            return {
                'id': user_data.get('id'),
                'username': user_data.get('slug'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'avatar_url': user_data.get('avatar_urls', {}).get('96', None)
            }
        
        current_app.logger.warning(f"获取WordPress用户失败: {response.status_code}")
        return None
    except Exception as e:
        current_app.logger.error(f"WordPress API请求失败: {str(e)}")
        return None

def create_wp_post(title, content, status='draft'):
    """创建WordPress文章
    
    Args:
        title: 文章标题
        content: 文章内容
        status: 文章状态，'draft' 或 'publish'
        
    Returns:
        dict: 成功时返回文章信息，失败时返回None
    """
    try:
        # 构建API URL
        api_url = current_app.config.get('WP_API_URL')
        if not api_url:
            current_app.logger.warning("WordPress API URL未配置")
            return None
        
        # 获取认证头
        try:
            headers = get_wp_api_headers()
        except ValueError:
            return None
        
        # 准备数据
        data = {
            'title': title,
            'content': content,
            'status': status
        }
        
        # 向WordPress API发送请求
        response = requests.post(
            f"{api_url}/wp/v2/posts", 
            headers=headers, 
            json=data,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code in [200, 201]:
            # 返回文章信息
            return response.json()
        
        current_app.logger.warning(f"创建WordPress文章失败: {response.status_code}")
        return None
    except Exception as e:
        current_app.logger.error(f"WordPress API请求失败: {str(e)}")
        return None