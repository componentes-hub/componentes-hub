from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired


class CreateCommunityForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    code = StringField('Code', validators=[DataRequired()])


class FindCommunityForm(FlaskForm):
    joinCode = StringField('joinCode', validators=[DataRequired()])


class UpdateCommunityForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    code = StringField('Code', validators=[DataRequired()])
