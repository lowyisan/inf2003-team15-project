from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(FlaskForm):
    
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=2, max=20)])
    
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    
    role = RadioField('Role', choices=[('homebuyer', 'Homebuyer'), ('agent', 'Agent')], validators=[DataRequired()])


    # Agent-specific fields
    CEANumber = StringField('CEA Number')  
    agencyLicenseNo = StringField('Agency License Number')  
    agentTitle = StringField('Agent Title')  
    
    phone = StringField('Phone',
                        validators=[DataRequired()])
    
    password = PasswordField('Password',
                             validators=[DataRequired()])
    
    confirm_password = PasswordField('Confirm Password',
                             validators=[DataRequired(), EqualTo('password')])
    
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    
    password = PasswordField('Password',
                             validators=[DataRequired()])
    
    remember = BooleanField('Remember Me')

    submit = SubmitField('Login')