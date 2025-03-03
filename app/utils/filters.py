from flask import Markup

def nl2br(value):
    """
    将文本中的换行符转换为HTML的<br>标签
    
    Args:
        value: 要转换的文本
        
    Returns:
        Markup: 转换后的 HTML 文本
    """
    if not value:
        return ''

    # 转义文本并将换行符替换为 <br>
    result = value.replace('\n', '<br>')
    return Markup(result)
