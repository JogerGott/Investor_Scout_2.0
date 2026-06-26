from typing import List, Optional
from app.repositories.base_repository import BaseRepository
from app.models.user import User

class ClienteRepository(BaseRepository):
    """
    Repository for the 'cliente' table in MySQL.
    """
    def save(self, user: User) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO cliente (nombre, apellido, email, password_hash, telefono)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    nombre = VALUES(nombre),
                    apellido = VALUES(apellido),
                    password_hash = VALUES(password_hash),
                    telefono = VALUES(telefono)
            """
            cursor.execute(query, (
                user.first_name,
                user.last_name,
                user.email,
                user.password_hash,
                user.telephone
            ))
            conn.commit()
            
            # Fetch the generated or existing id
            cursor.execute("SELECT id_cliente FROM cliente WHERE email = %s", (user.email,))
            res = cursor.fetchone()
            if res:
                user.user_id = res[0]
                return res[0]
            raise ValueError(f"Could not retrieve id_cliente for email {user.email}")
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_by_id(self, id_cliente: int) -> Optional[User]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_cliente, nombre, apellido, email, password_hash, telefono FROM cliente WHERE id_cliente = %s"
            cursor.execute(query, (id_cliente,))
            row = cursor.fetchone()
            if row:
                return User(
                    user_id=row["id_cliente"],
                    first_name=row["nombre"],
                    last_name=row["apellido"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    telephone=row["telefono"]
                )
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_by_email(self, email: str) -> Optional[User]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_cliente, nombre, apellido, email, password_hash, telefono FROM cliente WHERE email = %s"
            cursor.execute(query, (email,))
            row = cursor.fetchone()
            if row:
                return User(
                    user_id=row["id_cliente"],
                    first_name=row["nombre"],
                    last_name=row["apellido"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    telephone=row["telefono"]
                )
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_all(self) -> List[User]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_cliente, nombre, apellido, email, password_hash, telefono FROM cliente"
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                User(
                    user_id=row["id_cliente"],
                    first_name=row["nombre"],
                    last_name=row["apellido"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    telephone=row["telefono"]
                )
                for row in rows
            ]
        finally:
            cursor.close()
            self.close_connection(conn)
