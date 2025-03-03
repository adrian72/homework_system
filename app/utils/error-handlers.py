# app/utils/error_handlers.py
from flask import jsonify

def register_error_handlers(app):
    """注册全局错误处理程序"""
    
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            'error': 'Bad Request',
            'message': str(e) or '请求无效'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({
            'error': 'Unauthorized',
            'message': str(e) or '需要认证'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({
            'error': 'Forbidden',
            'message': str(e) or '禁止访问'
        }), 403
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            'error': 'Not Found',
            'message': str(e) or '资源不存在'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            'error': 'Method Not Allowed',
            'message': str(e) or '方法不允许'
        }), 405
    
    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({
            'error': 'Request Entity Too Large',
            'message': str(e) or '请求实体太大'
        }), 413
    
    @app.errorhandler(422)
    def unprocessable_entity(e):
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': str(e) or '无法处理的实体'
        }), 422
    
    @app.errorhandler(429)
    def too_many_requests(e):
        return jsonify({
            'error': 'Too Many Requests',
            'message': str(e) or '请求过多'
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e) or '服务器内部错误'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """处理未捕获的异常"""
        # 记录错误
        app.logger.error(f"未捕获的异常: {str(e)}")
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': '服务器遇到了一个错误'
        }), 500
