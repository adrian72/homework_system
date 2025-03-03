// app/static/js/main.js

/**
 * 通用API请求封装
 * @param {string} url - API路径
 * @param {string} method - 请求方法 (GET, POST, PUT, DELETE)
 * @param {object} data - 请求数据
 * @param {boolean} useFormData - 是否使用FormData格式
 * @returns {Promise} - 返回Promise对象
 */
function apiRequest(url, method = 'GET', data = null, useFormData = false) {
    // 设置请求选项
    const options = {
        method: method,
        headers: {}
    };
    
    // 获取JWT令牌
    const token = localStorage.getItem('auth_token');
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // 处理请求数据
    if (data) {
        if (useFormData) {
            // 使用FormData，不设置Content-Type头部
            options.body = data;
        } else {
            // 使用JSON
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        }
    }
    
    // 发送请求
    return fetch(url, options)
        .then(response => {
            // 检查响应状态
            if (response.ok) {
                return response.json();
            }
            
            // 处理401未授权错误
            if (response.status === 401) {
                // 清除令牌并重定向到登录页面
                localStorage.removeItem('auth_token');
                window.location.href = '/login';
                throw new Error('身份验证失败，请重新登录');
            }
            
            // 其他错误
            return response.json().then(err => {
                throw new Error(err.message || '请求失败');
            });
        });
}

/**
 * 显示通知
 * @param {string} message - 通知消息
 * @param {string} type - 通知类型 (success, info, warning, danger)
 * @param {number} duration - 显示时长(毫秒)
 */
function showNotification(message, type = 'info', duration = 3000) {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 添加样式
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '1050';
    notification.style.minWidth = '250px';
    notification.style.boxShadow = '0 0.5rem 1rem rgba(0, 0, 0, 0.15)';
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 创建Bootstrap警告对象
    const alert = new bootstrap.Alert(notification);
    
    // 设置自动关闭
    setTimeout(() => {
        alert.close();
    }, duration);
}

/**
 * 初始化状态标签
 */
function initStatusBadges() {
    document.querySelectorAll('[data-status]').forEach(element => {
        const status = element.getAttribute('data-status');
        const statusClass = `status-${status}`;
        element.classList.add('status-badge', statusClass);
        
        // 设置状态文本
        const statusTexts = {
            'submitted': '已提交',
            'graded': '已批改',
            'needs_revision': '需要修改',
            'revised': '已修改',
            'not_submitted': '未提交'
        };
        
        if (statusTexts[status]) {
            element.textContent = statusTexts[status];
        }
    });
}

/**
 * 初始化图片预览
 */
function initImagePreviews() {
    document.querySelectorAll('.image-preview-btn').forEach(button => {
        button.addEventListener('click', function() {
            const imageUrl = this.getAttribute('data-image-url');
            const title = this.getAttribute('data-title') || '图片预览';
            
            // 创建模态框
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'imagePreviewModal';
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body text-center">
                            <img src="${imageUrl}" class="img-fluid" alt="${title}">
                        </div>
                    </div>
                </div>
            `;
            
            // 添加到页面
            document.body.appendChild(modal);
            
            // 显示模态框
            const modalObj = new bootstrap.Modal(modal);
            modalObj.show();
            
            // 移除模态框
            modal.addEventListener('hidden.bs.modal', function() {
                document.body.removeChild(modal);
            });
        });
    });
}

/**
 * 初始化文件上传预览
 */
function initFileUploadPreviews() {
    document.querySelectorAll('.file-upload-input').forEach(input => {
        const previewContainer = document.getElementById(input.getAttribute('data-preview'));
        if (!previewContainer) return;
        
        input.addEventListener('change', function() {
            previewContainer.innerHTML = '';
            
            if (this.files.length === 0) return;
            
            // 处理图片上传
            if (this.accept.includes('image')) {
                Array.from(this.files).forEach(file => {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'image-preview mb-2 me-2';
                        img.style.maxHeight = '150px';
                        previewContainer.appendChild(img);
                    };
                    reader.readAsDataURL(file);
                });
            }
            
            // 处理音频上传
            else if (this.accept.includes('audio')) {
                Array.from(this.files).forEach(file => {
                    const audio = document.createElement('audio');
                    audio.controls = true;
                    audio.className = 'audio-player mb-2';
                    
                    const source = document.createElement('source');
                    source.src = URL.createObjectURL(file);
                    source.type = file.type;
                    
                    audio.appendChild(source);
                    previewContainer.appendChild(audio);
                });
            }
        });
    });
}

/**
 * 初始化页面
 */
document.addEventListener('DOMContentLoaded', function() {
    // 初始化状态标签
    initStatusBadges();
    
    // 初始化图片预览
    initImagePreviews();
    
    // 初始化文件上传预览
    initFileUploadPreviews();
    
    // 绑定表单验证事件
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});
