from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Association table for many-to-many relationship between Professional and Specialty
professional_specialty = db.Table('professional_specialty',
    db.Column('professional_id', db.Integer, db.ForeignKey('professional.id'), primary_key=True),
    db.Column('specialty_id', db.Integer, db.ForeignKey('specialty.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False, default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    professional = db.relationship('Professional', uselist=False, back_populates='user', cascade='all, delete-orphan')
    client = db.relationship('Client', uselist=False, back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_professional(self):
        return self.role == 'professional'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_client(self):
        return self.role == 'client'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    bio = db.Column(db.Text)
    address = db.Column(db.String(200))
    years_experience = db.Column(db.Integer)
    rating = db.Column(db.Float, default=0.0)
    accepts_insurance = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', back_populates='professional')
    specialties = db.relationship('Specialty', secondary=professional_specialty, backref='professionals')
    schedules = db.relationship('Schedule', back_populates='professional', cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', back_populates='professional', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Professional {self.user.username}>'

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    address = db.Column(db.String(200))
    insurance_info = db.Column(db.String(100))
    
    # Relationships
    user = db.relationship('User', back_populates='client')
    appointments = db.relationship('Appointment', back_populates='client', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Client {self.user.username}>'

class Specialty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Specialty {self.name}>'

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 1=Tuesday, etc.
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Relationships
    professional = db.relationship('Professional', back_populates='schedules')
    
    def __repr__(self):
        return f'<Schedule {self.professional.user.username} - Day: {self.day_of_week}>'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    professional = db.relationship('Professional', back_populates='appointments')
    client = db.relationship('Client', back_populates='appointments')
    
    def __repr__(self):
        return f'<Appointment {self.professional.user.username} - {self.client.user.username}>'
    
    def is_valid_time(self):
        """Check if appointment is within professional's schedule."""
        day_of_week = self.date.weekday()
        schedules = Schedule.query.filter_by(
            professional_id=self.professional_id,
            day_of_week=day_of_week
        ).all()
        
        for schedule in schedules:
            if (self.start_time >= schedule.start_time and 
                self.end_time <= schedule.end_time):
                return True
        return False
    
    def has_conflict(self):
        """Check if appointment conflicts with other appointments."""
        overlapping = Appointment.query.filter(
            Appointment.professional_id == self.professional_id,
            Appointment.date == self.date,
            Appointment.id != self.id,
            Appointment.status != 'cancelled',
            ((Appointment.start_time <= self.start_time) & (Appointment.end_time > self.start_time)) |
            ((Appointment.start_time < self.end_time) & (Appointment.end_time >= self.end_time)) |
            ((Appointment.start_time >= self.start_time) & (Appointment.end_time <= self.end_time))
        ).count()
        
        return overlapping > 0
