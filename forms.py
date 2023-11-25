from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField, SelectField, DecimalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange

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


class AddListingForm(FlaskForm):

    block = StringField('Block', validators=[DataRequired()])
    street_name = StringField('Street Name', validators=[DataRequired()])
    floorAreaSQM = StringField('Floor Area (SQM)', validators=[DataRequired()])
    town_estate = StringField('Town/Estate', validators=[DataRequired()])
    
    flat_type = SelectField('Flat Type', choices=[('3 ROOM', '3 ROOM'), ('4', '4 ROOM'), ('5 ROOM', '5 ROOM'), ('EXECUTIVE', 'EXECUTIVE')], validators=[DataRequired()])
    
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=100.00)]) 
    
    listing_desc = StringField('Listing Description')
    
    submit = SubmitField('Post Listing')