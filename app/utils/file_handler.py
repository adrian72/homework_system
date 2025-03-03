# app/utils/file_handler.py
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime
import magic
from PIL import Image
from pydub import AudioSegment

def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否在允许列表中"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, file_type='image'):
    """保存上传的文件
    
    Args:
        file: 上传的文件对象
        file_type: 文件类型，'image' 或 'audio'
        
    Returns:
        dict: 包含存储路径和元数据的字典
    """
    if file is None:
        return None
    
    # 检查文件类型
    if file_type == 'image':
        allowed_extensions = current_app.config['ALLOWED_IMAGE_EXTENSIONS']
    elif file_type == 'audio':
        allowed_extensions = current_app.config['ALLOWED_AUDIO_EXTENSIONS']
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")
    
    if not allowed_file(file.filename, allowed_extensions):
        raise ValueError(f"不允许的文件类型. 允许的类型: {', '.join(allowed_extensions)}")
    
    # 使用安全的文件名
    filename = secure_filename(file.filename)
    
    # 创建唯一的文件名
    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{str(uuid.uuid4())}.{ext}"
    
    # 创建基于日期的目录结构
    date_str = datetime.now().strftime('%Y%m%d')
    rel_path = os.path.join(file_type, date_str)
    abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], rel_path)
    
    # 确保目录存在
    os.makedirs(abs_path, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(abs_path, unique_filename)
    file.save(file_path)
    
    # 获取MIME类型
    mime_type = magic.from_file(file_path, mime=True)
    
    # 获取文件元数据
    result = {
        'filename': filename,
        'unique_filename': unique_filename,
        'path': os.path.join(rel_path, unique_filename),
        'url': f"/static/uploads/{rel_path}/{unique_filename}",
        'mime_type': mime_type,
        'size': os.path.getsize(file_path),
        'upload_time': datetime.now().isoformat()
    }
    
    # 处理特定类型的文件
    if file_type == 'image':
        try:
            with Image.open(file_path) as img:
                result.update({
                    'width': img.width,
                    'height': img.height,
                    'format': img.format
                })
        except Exception as e:
            print(f"无法处理图像文件: {e}")
    
    elif file_type == 'audio':
        try:
            audio = AudioSegment.from_file(file_path)
            result.update({
                'duration': len(audio) / 1000.0,  # 以秒为单位
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width
            })
        except Exception as e:
            print(f"无法处理音频文件: {e}")
    
    return result

def delete_file(file_path):
    """删除文件
    
    Args:
        file_path: 文件的相对路径
        
    Returns:
        bool: 是否成功删除
    """
    try:
        abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
            return True
        return False
    except Exception as e:
        print(f"删除文件时出错: {e}")
        return False
