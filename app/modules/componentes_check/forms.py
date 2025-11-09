from flask_wtf import FlaskForm
from wtforms import SubmitField

class ComponenteCheckForm(FlaskForm):
    submit = SubmitField('Save comp_check')