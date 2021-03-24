from flask import Blueprint, render_template


bp = Blueprint('help', __name__, url_prefix='')


@bp.route('/contact', methods=('GET', 'POST'))
def contact() -> str:
    return render_template('help/contact.html')


@bp.route('/data_policy', methods=('GET', 'POST'))
def data_policy() -> str:
    return render_template('help/data_policy.html')


@bp.route('/term_of_use')
def term_of_use() -> str:
    return render_template('help/term_of_use.html')
