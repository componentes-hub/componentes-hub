from app import db


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)

    orcid = db.Column(db.String(19))
    affiliation = db.Column(db.String(100))
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()
        
class UserFollowAuthor(db.Model):
    __tablename__ = "user_follow_author"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)

    user = db.relationship("User", backref="author_follows")
    author = db.relationship("Author", backref="user_follows")

class UserFollowUser(db.Model):
    __tablename__ = "user_follow_user"

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    follower = db.relationship("User", foreign_keys=[follower_id], backref="following_users")
    followed = db.relationship("User", foreign_keys=[followed_id], backref="user_followers")
