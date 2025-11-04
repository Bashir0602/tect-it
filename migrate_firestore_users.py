# migrate_firestore_users.py
from google.cloud import firestore

# 1. Initialize Firestore client
db = firestore.Client(project="tech-it-2025")

# 2. Correct Firestore paths based on your structure
# users → auth_users → user_data
src_ref = db.collection("users").document("auth_users").collection("user_data")
dst_ref = db.collection("users")

def migrate_users():
    print("Starting Firestore user migration...")
    count = 0

    # 3. Stream through every document in user_data
    for doc in src_ref.stream():
        data = doc.to_dict() or {}
        email = doc.id  # document ID (email)
        dst_ref.document(email).set(data)
        count += 1
        print(f"✓ Copied user: {email}")

    print(f"\nMigration finished successfully. {count} user(s) copied to top-level 'users' collection.")

if __name__ == "__main__":
    migrate_users()
