import os

from models import db, User, Message, Follows, Likes
from unittest import TestCase

os.environ['DATABASE_URL'] = 'postgresql:///warbler-test'

# must import after setting database
from app import app

class UserModelTestCase(TestCase):
    
    def setUp(self) -> None:
        db.drop_all()
        db.create_all()
        
        u = User.signup("username", "email@email.com", "password", None)
        db.session.commit()
        self.user = u
        
        return super().setUp()
    
    def tearDown(self) -> None:
        db.session.rollback()
    
    def test_messages(self):
        message = Message(text="a message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()
        
        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, "a message")
        
    def test_like_message(self):
        message = Message(text="a message", user_id=self.user.id)
        db.session.add(message)
        
        u2 = User.signup("username2", "email2@email.com", "password", None)
        
        u2.likes.append(message)
        db.session.commit()
        
        likes = Likes.query.filter(Likes.user_id == u2.id).all()
        self.assertEquals(len(likes), 1)
        self.assertEquals(likes[0].message_id, message.id)
        
    def test_delete_user_deletes_messages(self):
        message = Message(text="a message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()
        
        message_id = message.id
        
        db.session.delete(self.user)
        db.session.commit()
        
        deleted_message = Message.query.filter_by(id=message_id).first()
        self.assertIsNone(deleted_message)