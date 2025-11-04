from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client(project="tech-it-2025")

def delete_old_users():
    # ✅ Exact Firestore path
    user_data_ref = (
        db.collection("artifacts")
        .document("default-app-id")
        .collection("users")
        .document("auth_users")
        .collection("user_data")
    )

    # Fetch all documents in user_data
    users = list(user_data_ref.stream())

    if not users:
        print("⚠️ No documents found at artifacts/default-app-id/users/auth_users/user_data.")
        return

    print(f"Found {len(users)} user(s). Deleting...")

    # Delete each user document
    for doc in users:
        doc.reference.delete()
        print(f"🗑️ Deleted: {doc.id}")

    # Delete the empty auth_users document
    db.collection("artifacts").document("default-app-id").collection("users").document("auth_users").delete()
    print("✅ Deleted 'auth_users' and its subcollection 'user_data' successfully.")

if __name__ == "__main__":
    delete_old_users()
