from flask import Blueprint, render_template, redirect, url_for

main_views = Blueprint('main_views', __name__)

@main_views.route('/')
def index():
    """Home page route"""
    return render_template('index.html')
