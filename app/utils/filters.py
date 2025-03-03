from flask import Markup

def nl2br(value):
    """
    Convert line breaks to HTML line breaks
    """
    if not value:
        return ''

    result = value.replace('\n', '<br>')
    return Markup(result)
