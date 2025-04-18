from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user
from models import Specialty, Professional, User
from forms import SearchForm
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page with application information"""
    specialties = Specialty.query.order_by(Specialty.name).all()
    professionals_count = Professional.query.count()
    
    # Featured professionals (just a sample of 4 professionals)
    featured_professionals = db.session.query(Professional, User).join(User).limit(4).all()
    
    return render_template('index.html', 
                          specialties=specialties,
                          professionals_count=professionals_count,
                          featured_professionals=featured_professionals)

@main_bp.route('/search', methods=['GET', 'POST'])
def search():
    """Search for professionals by specialty and availability"""
    form = SearchForm()
    
    # Populate specialty choices
    specialties = Specialty.query.order_by(Specialty.name).all()
    form.specialty.choices = [(0, 'Todas las especialidades')] + [(s.id, s.name) for s in specialties]
    
    results = []
    
    if form.validate_on_submit() or request.method == 'GET' and 'specialty' in request.args:
        # Handle form submission or GET parameters
        specialty_id = form.specialty.data if request.method == 'POST' else request.args.get('specialty', type=int, default=0)
        date = form.date.data if request.method == 'POST' else None
        
        # Query for professionals
        query = db.session.query(Professional, User).join(User)
        
        # Filter by specialty if specified
        if specialty_id and specialty_id > 0:
            query = query.filter(Professional.specialties.any(id=specialty_id))
        
        # Apply pagination
        page = request.args.get('page', 1, type=int)
        pagination = query.paginate(page=page, per_page=12, error_out=False)
        results = pagination.items
        
        return render_template('search.html', form=form, results=results, 
                              pagination=pagination, specialty_id=specialty_id)
    
    return render_template('search.html', form=form, results=results)

@main_bp.route('/professional/<int:professional_id>')
def professional_profile(professional_id):
    """View a professional's profile and availability"""
    professional = Professional.query.get_or_404(professional_id)
    user = User.query.get(professional.user_id)
    
    if not professional or not user:
        flash('Profesional no encontrado.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('professional_profile.html', professional=professional, user=user)
