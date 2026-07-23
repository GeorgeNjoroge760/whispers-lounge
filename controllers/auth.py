from models.user import UserModel


class AuthController:
    def __init__(self, db):
        self.user_model = UserModel(db)
        self.current_user = None

    def login(self, username, password):
        user = self.user_model.authenticate(username, password)
        if user:
            self.current_user = user
            return True, "Login successful"
        return False, "Invalid username or password"

    def set_current_user(self, user):
        self.current_user = dict(user) if not isinstance(user, dict) else user

    def logout(self):
        self.current_user = None

    def get_current_user(self):
        return self.current_user

    def get_all_staff(self):
        return [dict(u) for u in self.user_model.get_all(active_only=True)]

    def has_role(self, role):
        if not self.current_user:
            return False
        from config import ROLES
        return ROLES.get(self.current_user["role"], {}).get("level", 0) >= ROLES.get(role, {}).get("level", 99)

    def can_manage_users(self):
        return self.has_role("admin")

    def can_manage_inventory(self):
        return self.has_role("manager")

    def can_view_reports(self):
        return self.has_role("manager")
