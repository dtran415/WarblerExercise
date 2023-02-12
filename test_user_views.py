import os
from unittest import TestCase
from models import db, User, Message
from flask import session
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# must import after setting database
from app import app, CURR_USER_KEY
app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    
    def setUp(self) -> None:
        db.drop_all()
        db.create_all()
        self.client = app.test_client()
        
        user = User.signup("testuser", "test@email.com", "password1", None)
        user2 = User.signup("testuser2", "test2@email.com", "password2", None)
        User.signup("testuser3", "test3@email.com", "password3", None)
        User.signup("testuser4", "test4@email.com", "password4", None)
        
        user.followers.append(user2)
        
        db.session.commit()
        
        db.session.add(Message(text="message here", user_id=user.id))
        db.session.add(Message(text="message2 here", user_id=user2.id))
        
        db.session.commit()
        
        return super().setUp()
    
    def tearDown(self) -> None:
        db.session.rollback()
        return super().tearDown()
    
    def test_login(self):
        with self.client as c:
            resp = c.get('/login')
            self.assertIn("username", str(resp.data))
            self.assertIn("password", str(resp.data))
            
            resp = c.post('/login', data={'username':'testuser', 'password':'password1'}, content_type="application/x-www-form-urlencoded", follow_redirects=True)
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            user_tag = soup.find("p", string="@testuser")
            self.assertIsNotNone(user_tag)
            
    def test_logout(self):
        with self.client as c:
            user = User.query.filter_by(username='testuser').first()
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
                
            resp = c.get('/logout', follow_redirects=True)
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            signup_link = soup.find('a', href='/signup')
            self.assertIsNotNone(signup_link)
            
            login_link = soup.find('a', href='/login')
            self.assertIsNotNone(login_link)
            
            self.assertFalse(CURR_USER_KEY in session)
            
    def test_sign_up(self):
        with self.client as c:
            resp = c.get("/signup")
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            self.assertIsNotNone(soup.find('input', id='username'))
            self.assertIsNotNone(soup.find('input', id='email'))
            self.assertIsNotNone(soup.find('input', id='password'))
            self.assertIsNotNone(soup.find('input', id='image_url'))
            
            resp = c.post('/signup', data={'username':'testuser5', 'email':'email5@email.com', 'password':'password5'}, content_type="application/x-www-form-urlencoded", follow_redirects=True)
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            self.assertIsNotNone(soup.find('a', href='/logout'))
            
    def test_sign_up_duplicate_user(self):
        with self.client as c:            
            resp = c.post('/signup', data={'username':'testuser', 'email':'email5@email.com', 'password':'password5'}, content_type="application/x-www-form-urlencoded", follow_redirects=True)
            self.assertIn("Username already taken", str(resp.data))
        
    def test_home_page(self):
        with self.client as c:
            resp = c.get("/")
            soup = BeautifulSoup(str(resp.data), "html.parser")
            self.assertIsNotNone(soup.find(string="New to Warbler?"))
            
            resp = c.post('/login', data={'username':'testuser', 'password':'password1'}, content_type="application/x-www-form-urlencoded", follow_redirects=True)
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            self.assertIsNotNone(soup.find(string="message here"))
            self.assertIsNotNone(soup.find(string="message2 here"))
            
    def test_users_page(self):
        with self.client as c:
            resp = c.get("/users")
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            user_cards = soup.find_all(class_='user-card')
            self.assertEqual(len(user_cards), 4)
            self.assertIsNotNone(soup.find(string='@testuser'))
            
    def test_users_search(self):
        with self.client as c:
            resp = c.get("/users?q=testuser4")
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            user_cards = soup.find_all(class_='user-card')
            self.assertEqual(len(user_cards), 1)
            self.assertIsNotNone(soup.find(string='@testuser4'))
            
    def test_user_profile(self):
        with self.client as c:
            user = User.query.filter_by(username='testuser').first()
            # log in with one user
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
                
            resp = c.get(f"/users/{user.id}")
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            self.assertIsNotNone(soup.find(class_='user-stats'))
            
            # Follow should not show up since we're on logged in user's page
            self.assertIsNone(soup.find('button', string='Follow'))
            
            user2 = User.query.filter_by(username='testuser2').first()
            
            resp = c.get(f"/users/{user2.id}")
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            # Follow should show up since we're looking at a different person's profile page
            self.assertIsNotNone(soup.find('button', string='Follow'))
            
    def test_following_page(self):
        with self.client as c:
            user = User.query.filter_by(username='testuser2').first()
            
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
            
            # user2 is following user in setup
            resp = c.get(f"/users/{user.id}/following")
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            user1 = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(soup.find(string=f'@{user1.username}'))
            
    def test_followers_page(self):
        with self.client as c:
            user = User.query.filter_by(username='testuser').first()
            
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
            
            # user2 is following user in setup
            resp = c.get(f"/users/{user.id}/followers")
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            user1 = User.query.filter_by(username='testuser2').first()
            self.assertIsNotNone(soup.find(string=f'@{user1.username}'))
            
    def test_follow(self):
        with self.client as c:
            user = User.query.filter_by(username='testuser3').first()
            
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
            
            # have testuser3 follow testuser2
            user2 = User.query.filter_by(username='testuser2').first()
            
            resp = c.post(f"/users/follow/{user2.id}", follow_redirects=True)
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            # should redirect to testuser3's following page and see testuser2 in html
            self.assertIsNotNone(soup.find(string=f'@{user2.username}'))
            
    def test_stop_following(self):
        with self.client as c:
            # testuser2 is following testuser in setup
            user = User.query.filter_by(username='testuser2').first()
            
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
            
            # have testuser2 stop following testuser
            user2 = User.query.filter_by(username='testuser').first()
            
            resp = c.post(f"/users/stop-follow/{user.id}", follow_redirects=True)
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            # should redirect to testuser2's following page and not see testuser in html
            self.assertIsNone(soup.find(string=f'@{user.username}'))
            
    def test_edit_profile(self):
        with self.client as c:
            user = User.query.filter_by(username='testuser').first()
            
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
                
            resp = c.post(f"/users/profile", data={'username':'newname', 'password':'password1', 'email':'newemail@email.com', 'bio':'new bio'}, content_type="application/x-www-form-urlencoded", follow_redirects=True)
            
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            self.assertIsNotNone(soup.find(string='@newname'))
            self.assertIsNotNone(soup.find(string='new bio'))
            self.assertEqual(user.email, 'newemail@email.com')
            
    def test_delete_user(self):
        with self.client as c:
            user = User.query.filter_by(username='testuser').first()
            
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
                
            resp = c.post("/users/delete", follow_redirects=True)
            
            # should redirect to signup page
            soup = BeautifulSoup(str(resp.data), "html.parser")
            
            self.assertIsNotNone(soup.find(string='Sign me up!'))
            
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNone(user)