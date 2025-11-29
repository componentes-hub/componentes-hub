from app import db


class CommunityUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f'CommunityUsers<{self.id}, {self.community_id}, {self.user_id}>'


class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    users = db.relationship('CommunityUser', backref='community', lazy=True)

    def __repr__(self):
        return f'Community<{self.id}, {self.name}>'
