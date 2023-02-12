"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()
        u = User.signup("username", "email@email.com", "password", None)
        db.session.commit()
        self.user = u
        
    def tearDown(self) -> None:
        db.session.rollback()
        return super().tearDown()

    def test_user_model(self):
        """Does basic model work?"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()
        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(u.image_url, '/static/images/default-pic.png')
        self.assertEqual(u.header_image_url, '/static/images/warbler-hero.jpg')
        
    def test_repr(self):
        u = self.user
        self.assertEqual(u.__repr__(), f"<User #{u.id}: username, email@email.com>")
    
    def test_sign_up(self):
        
        user = User.query.filter_by(username="username").one()
        self.assertIsNotNone(user)
    
    def test_authenticate_with_good_username_password(self):
        result = User.authenticate('username', 'password')
        self.assertTrue(result)
        
    def test_authenticate_with_bad_username_password(self):
        result = User.authenticate('username1', 'password')
        self.assertFalse(result)
        
    def test_user_already_exists(self):
        User.signup("username", "email2@email.com", "password", None)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
            
    def test_user_follow(self):
        u2 = User.signup("username2", "email2@email.com", "password", None)
        u1 = self.user
        
        u1.followers.append(u2)
        db.session.commit()
        self.assertEqual(len(u1.following), 0)
        self.assertEqual(len(u2.following), 1)
        self.assertEqual(len(u1.followers), 1)
        self.assertEqual(len(u2.followers), 0)
        
    def test_user_follow(self):
        u2 = User.signup("username2", "email2@email.com", "password", None)
        u1 = self.user
        
        u1.followers.append(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertTrue(u2.is_following(u1))
        self.assertTrue(u1.is_followed_by(u2))
        self.assertFalse(u2.is_followed_by(u1))
        
    def test_delete_user(self):
        # add a second user to test if followers table gets updated
        u2 = User.signup("username2", "email2@email.com", "password", None)
        u1 = self.user
        
        u1.followers.append(u2)
        db.session.commit()
        
        db.session.delete(u1)
        db.session.commit()
        
        user = User.query.filter_by(username="username").first()
        self.assertIsNone(user)
        
        self.assertEquals(len(u2.following), 0)