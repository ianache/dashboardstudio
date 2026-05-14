
import sys
import os
from sqlalchemy.orm import Session

# Add the current directory to sys.path to import app
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models import models

def check_user(user_id):
    print(f"Checking if user {user_id} exists...")
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            print(f"User found: {user.username} (ID: {user.id})")
        else:
            print(f"USER NOT FOUND: {user_id}")
            
            # List some users to see what's there
            print("\nExisting users in DB:")
            users = db.query(models.User).limit(5).all()
            for u in users:
                print(f"- {u.id}: {u.username}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    target_id = "204c973e-9312-4713-b3fe-86a4ff8607a2"
    check_user(target_id)
