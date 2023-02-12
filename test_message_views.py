"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User
from bs4 import BeautifulSoup

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

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
        
    def tearDown(self) -> None:
        db.session.rollback()
        return super().tearDown()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            user = User.query.filter_by(username='testuser').first()
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.filter_by(text='Hello')
            self.assertIsNotNone(msg)

    def test_get_message(self):
        with self.client as c:
            msg = Message.query.first()
            resp = c.get(f"/messages/{msg.id}")

            soup = BeautifulSoup(str(resp.data), 'html.parser')
            self.assertIsNotNone(soup.find(string=msg.text))
            
    def test_delete_message(self):
        with self.client as c:
            msg = Message.query.first()
            
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = msg.user_id
            
            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)

            soup = BeautifulSoup(str(resp.data), 'html.parser')
            self.assertIsNone(soup.find(string=msg.text))
            self.assertIsNone(Message.query.get(msg.id))
            
    def test_like_message(self):
        
        # have testuser like testuser2's message
        user = User.query.filter_by(username='testuser').first()
        user2 = User.query.filter_by(username='testuser2').first()
        
        msg = user2.messages[0]
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
            
            c.post(f"/users/add_like/{msg.id}", follow_redirects=True)
            
            self.assertEqual(user.likes[0].text,msg.text)
            
            #also test unlike
            c.post(f"/users/add_like/{msg.id}", follow_redirects=True)
            
            self.assertEqual(len(user.likes), 0)
    
    def test_like_page(self):
        # have testuser like testuser2's message
        user = User.query.filter_by(username='testuser').first()
        user2 = User.query.filter_by(username='testuser2').first()
        
        msg = user2.messages[0]
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
            
            c.post(f"/users/add_like/{msg.id}", follow_redirects=True)
            
            resp = c.get(f'/users/{user.id}/likes')
            
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            self.assertIsNotNone(soup.find(string=msg.text))
            
    def test_remove_like_from_likes_page(self):
        # have testuser like testuser2's message
        user = User.query.filter_by(username='testuser').first()
        user2 = User.query.filter_by(username='testuser2').first()
        
        msg = user2.messages[0]
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
            
            c.post(f"/users/add_like/{msg.id}", follow_redirects=True)
            
            resp = c.post(f'/likes/{msg.id}', follow_redirects=True)
            
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            
            # should end up back at likes page with like gone
            self.assertIsNone(soup.find(string=msg.text))