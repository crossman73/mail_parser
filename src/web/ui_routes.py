from flask import Blueprint, render_template

# [2025-12-30] UI Blueprint
# url_prefix='': 실험적 UI 경로 ('/ui/wireframe')
# admin과 url_prefix 충돌 가능성 있음 - Phase 2에서 정리 예정
ui = Blueprint('ui', __name__, url_prefix='')


@ui.route('/ui/wireframe')
def wireframe():
    return render_template('ui_wireframe.html')
