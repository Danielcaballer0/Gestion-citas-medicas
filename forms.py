from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField
from wtforms import DateField, TimeField, SelectMultipleField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    first_name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=64)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=64)])
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Teléfono', validators=[Optional(), Length(min=6, max=20)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Tipo de Usuario', choices=[('client', 'Cliente'), ('professional', 'Profesional')])
    specialty = SelectField('Especialidad', coerce=int, validators=[Optional()])
    submit = SubmitField('Registrarse')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Este nombre de usuario ya está en uso. Por favor, utiliza otro.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Este email ya está registrado. Por favor, utiliza otro.')

class ClientProfileForm(FlaskForm):
    first_name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=64)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=64)])
    phone = StringField('Teléfono', validators=[Optional(), Length(min=6, max=20)])
    address = StringField('Dirección', validators=[Optional(), Length(max=200)])
    insurance_info = StringField('Información de Seguro', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Guardar Cambios')

class ProfessionalProfileForm(FlaskForm):
    first_name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=64)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=64)])
    phone = StringField('Teléfono', validators=[Optional(), Length(min=6, max=20)])
    address = StringField('Dirección', validators=[Optional(), Length(max=200)])
    bio = TextAreaField('Biografía', validators=[Optional(), Length(max=1000)])
    years_experience = IntegerField('Años de Experiencia', validators=[Optional()])
    specialties = SelectMultipleField('Especialidades', coerce=int)
    accepts_insurance = BooleanField('Acepta Seguros')
    submit = SubmitField('Guardar Cambios')

class ScheduleForm(FlaskForm):
    day_of_week = SelectField('Día de la Semana', choices=[
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'),
        (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo')
    ], coerce=int)
    start_time = TimeField('Hora de Inicio', validators=[DataRequired()])
    end_time = TimeField('Hora de Fin', validators=[DataRequired()])
    submit = SubmitField('Guardar Horario')
    
    def validate_end_time(self, end_time):
        if end_time.data <= self.start_time.data:
            raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')

class AppointmentForm(FlaskForm):
    date = DateField('Fecha', validators=[DataRequired()])
    start_time = TimeField('Hora de Inicio', validators=[DataRequired()])
    end_time = TimeField('Hora de Fin', validators=[DataRequired()])
    notes = TextAreaField('Notas', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Reservar Cita')
    
    def validate_end_time(self, end_time):
        if end_time.data <= self.start_time.data:
            raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')

class SearchForm(FlaskForm):
    specialty = SelectField('Especialidad', coerce=int)
    date = DateField('Fecha', validators=[Optional()])
    submit = SubmitField('Buscar')

class SpecialtyForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Guardar Especialidad')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Contraseña Actual', validators=[DataRequired()])
    new_password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', 
                                    validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Cambiar Contraseña')

class AppointmentStatusForm(FlaskForm):
    status = SelectField('Estado', choices=[
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
        ('completed', 'Completada')
    ])
    notes = TextAreaField('Notas', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Actualizar Estado')
