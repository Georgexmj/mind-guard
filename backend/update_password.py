"""Script to update user password"""
import sys
sys.path.insert(0, '/app')

from app.core.security import hash_password
from app.database import SessionLocal, engine
from app.models.user import User

# Import models to register them
import app.models.assessment
import app.models.intervention
import app.models.user
import app.models.notification
import app.models.rag

db = SessionLocal()

try:
    user = db.query(User).filter(User.id_card == '123456194808151234').first()
    if user:
        user.password_hash = hash_password('elder123')
        db.commit()
        print(f"Password updated for user: {user.name} ({user.id_card})")
    else:
        print("User not found")
finally:
    db.close()
