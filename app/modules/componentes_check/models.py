from app import db

class ComponenteCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)