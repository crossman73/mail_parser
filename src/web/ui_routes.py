from flask import Blueprint, render_template

ui = Blueprint('ui', __name__, url_prefix='')


@ui.route('/ui/wireframe')
def wireframe():
    return render_template('ui_wireframe.html')
