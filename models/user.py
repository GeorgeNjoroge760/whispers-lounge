from utils.validators import Validators


class UserModel:
    def __init__(self, db):
        self.db = db

    def get_all(self, active_only=False):
        q = "SELECT id, username, full_name, role, is_active, created_at FROM users"
        if active_only:
            q += " WHERE is_active = 1"
        q += " ORDER BY created_at DESC"
        return self.db.fetchall(q)

    def get_by_id(self, user_id):
        return self.db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))

    def get_by_username(self, username):
        return self.db.fetchone("SELECT * FROM users WHERE username = ?", (username,))

    def create(self, username, password, full_name, role="attendant"):
        import bcrypt
        Validators.username(username)
        Validators.password(password)
        Validators.not_empty(full_name, "Full name")
        if self.get_by_username(username):
            raise ValueError(f"Username '{username}' already exists")
        pwd_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        self.db.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (username, pwd_hash, full_name, role),
        )

    def update(self, user_id, full_name=None, role=None, is_active=None):
        fields, vals = [], []
        if full_name is not None:
            fields.append("full_name = ?")
            vals.append(full_name)
        if role is not None:
            fields.append("role = ?")
            vals.append(role)
        if is_active is not None:
            fields.append("is_active = ?")
            vals.append(int(is_active))
        if not fields:
            return
        vals.append(user_id)
        self.db.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", tuple(vals))

    def change_password(self, user_id, new_password):
        import bcrypt
        Validators.password(new_password)
        pwd_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        self.db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, user_id))

    def authenticate(self, username, password):
        import bcrypt
        user = self.get_by_username(username)
        if not user:
            return None
        if not user["is_active"]:
            return None
        if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return dict(user)
        return None

    def delete(self, user_id):
        self.db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
