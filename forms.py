from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[DataRequired(message='This field is required')])
    password = PasswordField('Password', validators=[DataRequired(message='This field is required')])


class SignupForm(FlaskForm):
    """Form for new user signup"""

    username = StringField('Username', validators=[DataRequired(message='This field is required'), Length(max=25)])
    password = PasswordField('Password', validators=[Length(min=8, message='Password must be 8 or more characters'), DataRequired(message='This field is required')] )

class PlaylistForm(FlaskForm):
    """Form for creating a new playlist"""

    name = StringField('Playlist Name', validators=[DataRequired(message='This field is required')])
    description = StringField('Playlist Description (optional)')