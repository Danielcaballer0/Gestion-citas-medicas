import unittest
from datetime import datetime, timedelta
from app import app, db
from models import User, Client, Professional, Appointment, Specialty

class TestGestorCitas(unittest.TestCase):
    """Test suite for Gestor de Citas para Profesionales application"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory database
        
        # Create test client
        self.client = app.test_client()
        
        # Create application context
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Create test specialty
        try:
            specialty = Specialty(name="Psicología")
            db.session.add(specialty)
            db.session.commit()
            print("Created test specialty")
        except Exception as e:
            db.session.rollback()
            print(f"Note: {str(e)}")
            specialty = Specialty.query.filter_by(name="Psicología").first()
        
        print("Test environment set up successfully")
    
    def tearDown(self):
        """Clean up after each test"""
        db.session.close()
        db.drop_all()
        self.app_context.pop()
        print("Test environment cleaned up")
    
    def test_register_client(self):
        """Test client registration functionality"""
        print("\nRunning test_register_client...")
        
        # Create registration data for a client
        data = {
            'username': 'testclient',
            'email': 'client@test.com',
            'password': 'password123',
            'password2': 'password123',
            'first_name': 'Test',
            'last_name': 'Client',
            'phone': '1234567890',
            'role': 'client'
        }
        
        # Submit registration form
        response = self.client.post('/register', data=data, follow_redirects=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Verify user was created in database
        user = User.query.filter_by(email='client@test.com').first()
        if user:
            print("✅ Test passed: Client user created successfully")
            self.assertEqual(user.username, 'testclient')
            self.assertEqual(user.role, 'client')
            
            # Verify client profile was created
            client = Client.query.filter_by(user_id=user.id).first()
            if client:
                print("✅ Test passed: Client profile created successfully")
            else:
                print("❌ Test failed: Client profile not created")
                self.assertIsNotNone(client)
        else:
            print("❌ Test failed: Client user not created")
            self.assertIsNotNone(user)
    
    def test_login(self):
        """Test login functionality"""
        print("\nRunning test_login...")
        
        # Create a test user
        try:
            user = User(
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                role='client'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            print("Created test user for login")
            
            # Create client profile
            client = Client(user_id=user.id)
            db.session.add(client)
            db.session.commit()
            print("Created client profile for login test")
            
            # Attempt login with correct credentials
            response = self.client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            
            # Check response
            self.assertEqual(response.status_code, 200)
            print("✅ Test passed: Login response code is 200")
            
            # Test login with incorrect password
            response = self.client.post('/login', data={
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }, follow_redirects=True)
            
            # Check for error message
            if b'Email o contrase' in response.data:  # 'Email o contraseña incorrectos'
                print("✅ Test passed: Login with wrong password shows error message")
            else:
                print("❌ Test failed: Login error message not found")
                self.assertIn(b'Email o contrase', response.data)
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            self.fail(f"Login test failed with error: {str(e)}")
    
    def test_protected_routes(self):
        """Test access to protected routes requires login"""
        print("\nRunning test_protected_routes...")
        
        # Test access to client protected route without login
        response = self.client.get('/client/my_appointments', follow_redirects=True)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 200)
        if b'login' in response.data.lower():
            print("✅ Test passed: Unauthenticated access redirects to login")
        else:
            print("❌ Test failed: Unauthenticated access did not redirect to login")
            self.assertIn(b'login', response.data.lower())
            
    def test_book_appointment(self):
        """Test appointment booking functionality"""
        print("\nRunning test_book_appointment...")
        
        try:
            # Create professional user
            pro_user = User(
                username='testpro',
                email='pro@test.com',
                first_name='Pro',
                last_name='Test',
                role='professional'
            )
            pro_user.set_password('password123')
            db.session.add(pro_user)
            db.session.flush()
            
            # Create professional profile
            professional = Professional(user_id=pro_user.id)
            specialty = Specialty.query.first()
            if specialty:
                professional.specialties.append(specialty)
            db.session.add(professional)
            
            # Create client user
            client_user = User(
                username='testclient',
                email='client@test.com',
                first_name='Client',
                last_name='Test',
                role='client'
            )
            client_user.set_password('password123')
            db.session.add(client_user)
            db.session.flush()
            
            # Create client profile
            client = Client(user_id=client_user.id)
            db.session.add(client)
            db.session.commit()
            print("Created test users and profiles")
            
            # Login as client
            self.client.post('/login', data={
                'email': 'client@test.com',
                'password': 'password123'
            })
            
            # Book an appointment
            tomorrow = datetime.now() + timedelta(days=1)
            appointment_data = {
                'date': tomorrow.strftime('%Y-%m-%d'),
                'start_time': '10:00',
                'end_time': '11:00',
                'notes': 'Test appointment'
            }
            
            response = self.client.post(f'/client/book_appointment/{professional.id}', 
                                      data=appointment_data, 
                                      follow_redirects=True)
            
            # Check response
            self.assertEqual(response.status_code, 200)
            print("✅ Test passed: Booking response code is 200")
            
            # Verify appointment was created
            appointment = Appointment.query.filter_by(
                client_id=client.id,
                professional_id=professional.id
            ).first()
            
            if appointment:
                print("✅ Test passed: Appointment was created")
                self.assertEqual(appointment.notes, 'Test appointment')
            else:
                print("❌ Test failed: Appointment was not created")
                self.assertIsNotNone(appointment)
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            self.fail(f"Appointment booking test failed with error: {str(e)}")
    
    def test_cancel_appointment(self):
        """Test appointment cancellation functionality"""
        print("\nRunning test_cancel_appointment...")
        
        try:
            # Create professional user
            pro_user = User(
                username='testpro',
                email='pro@test.com',
                first_name='Pro',
                last_name='Test',
                role='professional'
            )
            pro_user.set_password('password123')
            db.session.add(pro_user)
            db.session.flush()
            
            # Create professional profile
            professional = Professional(user_id=pro_user.id)
            db.session.add(professional)
            
            # Create client user
            client_user = User(
                username='testclient',
                email='client@test.com',
                first_name='Client',
                last_name='Test',
                role='client'
            )
            client_user.set_password('password123')
            db.session.add(client_user)
            db.session.flush()
            
            # Create client profile
            client = Client(user_id=client_user.id)
            db.session.add(client)
            
            # Create appointment
            tomorrow = datetime.now() + timedelta(days=1)
            appointment = Appointment(
                client_id=client.id,
                professional_id=professional.id,
                date=tomorrow.date(),
                start_time='10:00',
                end_time='11:00',
                status='confirmed',
                notes='Test appointment'
            )
            db.session.add(appointment)
            db.session.commit()
            print("Created test appointment")
            
            # Login as client
            self.client.post('/login', data={
                'email': 'client@test.com',
                'password': 'password123'
            })
            
            # Cancel the appointment
            response = self.client.post(f'/client/cancel_appointment/{appointment.id}', 
                                      follow_redirects=True)
            
            # Check response
            self.assertEqual(response.status_code, 200)
            print("✅ Test passed: Cancellation response code is 200")
            
            # Verify appointment was cancelled
            updated_appointment = Appointment.query.get(appointment.id)
            if updated_appointment and updated_appointment.status == 'cancelled':
                print("✅ Test passed: Appointment was cancelled successfully")
            else:
                print("❌ Test failed: Appointment was not cancelled")
                self.assertEqual(updated_appointment.status, 'cancelled')
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            self.fail(f"Appointment cancellation test failed with error: {str(e)}")


if __name__ == '__main__':
    unittest.main()
        pro_user = User(
            username='testpro',
            email='pro@test.com',
            first_name='Pro',
            last_name='Test',
            role='professional'
        )
        pro_user.set_password('password123')
        db.session.add(pro_user)
        db.session.flush()
        
        professional = Professional(user_id=pro_user.id)
        db.session.add(professional)
        
        # 2. Create two clients
        client1_user = User(
            username='client1',
            email='client1@test.com',
            first_name='Client1',
            last_name='Test',
            role='client'
        )
        client1_user.set_password('password123')
        db.session.add(client1_user)
        db.session.flush()
        
        client1 = Client(user_id=client1_user.id)
        db.session.add(client1)
        
        client2_user = User(
            username='client2',
            email='client2@test.com',
            first_name='Client2',
            last_name='Test',
            role='client'
        )
        client2_user.set_password('password123')
        db.session.add(client2_user)
        db.session.flush()
        
        client2 = Client(user_id=client2_user.id)
        db.session.add(client2)
        db.session.commit()
        
        # Create first appointment
        tomorrow = datetime.now() + timedelta(days=1)
        appointment1 = Appointment(
            client_id=client1.id,
            professional_id=professional.id,
            date=tomorrow.date(),
            start_time='10:00',
            end_time='11:00',
            status='confirmed',
            notes='First appointment'
        )
        db.session.add(appointment1)
        db.session.commit()
        
        # Login as second client
        self.client.post('/login', data={
            'email': 'client2@test.com',
            'password': 'password123'
        })
        
        # Try to book an appointment at the same time
        appointment_data = {
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '11:00',
            'notes': 'Second appointment'
        }
        
        response = self.client.post(f'/client/book_appointment/{professional.id}', 
                                   data=appointment_data, 
                                   follow_redirects=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Verify that no new appointment was created for the same time slot
        appointments = Appointment.query.filter_by(
            professional_id=professional.id,
            date=tomorrow.date(),
            start_time='10:00'
        ).all()
        
        self.assertEqual(len(appointments), 1)
        self.assertEqual(appointments[0].client_id, client1.id)
        
        print("✅ Test passed: Double booking prevention works correctly")
    
    def test_authorized_access(self):
        """Test access control to protected routes"""
        print("\nRunning test_authorized_access...")
        
        # Create test users
        client_user = User(
            username='testclient',
            email='client@test.com',
            first_name='Client',
            last_name='Test',
            role='client'
        )
        client_user.set_password('password123')
        db.session.add(client_user)
        db.session.flush()
        
        client = Client(user_id=client_user.id)
        db.session.add(client)
        
        pro_user = User(
            username='testpro',
            email='pro@test.com',
            first_name='Pro',
            last_name='Test',
            role='professional'
        )
        pro_user.set_password('password123')
        db.session.add(pro_user)
        db.session.flush()
        
        professional = Professional(user_id=pro_user.id)
        db.session.add(professional)
        db.session.commit()
        
        # Test 1: Unauthenticated access to protected route
        response = self.client.get('/client/my_appointments', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Por favor inicia sesi', response.data)  # Should be redirected to login
        
        # Test 2: Client accessing professional route
        self.client.post('/login', data={
            'email': 'client@test.com',
            'password': 'password123'
        })
        
        response = self.client.get('/professional/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No tienes permisos', response.data)  # Access denied message
        
        # Logout client
        self.client.get('/logout')
        
        # Test 3: Professional accessing client route
        self.client.post('/login', data={
            'email': 'pro@test.com',
            'password': 'password123'
        })
        
        response = self.client.get('/client/my_appointments', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No tienes permisos', response.data)  # Access denied message
        
        print("✅ Test passed: Access control works correctly")


if __name__ == '__main__':
    unittest.main()
