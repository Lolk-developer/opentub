from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_id, username, email, password_hash, date_joined, is_verified, profile_picture, bio, role):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.date_joined = date_joined
        self.is_verified = is_verified
        self.profile_picture = profile_picture
        self.bio = bio
        self.role = role

    def get_id(self):
        return str(self.id)