import hashlib


class AuthController:
    def __init__(self, db_manager):
        self.db = db_manager
        self.current_user = None

    def login(self, username, password):
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        query = "SELECT id, username, rol FROM usuarios WHERE username=? AND password_hash=?"
        user = self.db.cursor.execute(query, (username, pwd_hash)).fetchone()

        if user:
            self.current_user = user  # (id, username, rol)
            return True
        return False
