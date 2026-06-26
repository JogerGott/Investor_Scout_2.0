from typing import List, Optional
from app.repositories.base_repository import BaseRepository
from app.models.portfolio import Portfolio

class PortafolioRepository(BaseRepository):
    """
    Repository for the 'portafolio' table in MySQL.
    """
    def save(self, portfolio: Portfolio) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO portafolio (id_cliente, nombre_portafolio, perfil_riesgo, cash)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    nombre_portafolio = VALUES(nombre_portafolio),
                    perfil_riesgo = VALUES(perfil_riesgo),
                    cash = VALUES(cash)
            """
            cursor.execute(query, (
                portfolio.user_id,
                portfolio.name,
                "MODERADO",
                portfolio.cash_balance
            ))
            conn.commit()
            
            # Fetch generated ID
            if portfolio.portfolio_id:
                return portfolio.portfolio_id
            cursor.execute("SELECT LAST_INSERT_ID()")
            res = cursor.fetchone()
            if res:
                portfolio.portfolio_id = res[0]
                return res[0]
            raise ValueError("Could not retrieve id_portafolio after save.")
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_by_id(self, id_portafolio: int) -> Optional[Portfolio]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_portafolio, id_cliente, nombre_portafolio, cash FROM portafolio WHERE id_portafolio = %s"
            cursor.execute(query, (id_portafolio,))
            row = cursor.fetchone()
            if row:
                return Portfolio(
                    portfolio_id=row["id_portafolio"],
                    user_id=row["id_cliente"],
                    name=row["nombre_portafolio"],
                    cash_balance=float(row["cash"])
                )
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_all_by_cliente(self, id_cliente: int) -> List[Portfolio]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_portafolio, id_cliente, nombre_portafolio, cash FROM portafolio WHERE id_cliente = %s"
            cursor.execute(query, (id_cliente,))
            rows = cursor.fetchall()
            return [
                Portfolio(
                    portfolio_id=row["id_portafolio"],
                    user_id=row["id_cliente"],
                    name=row["nombre_portafolio"],
                    cash_balance=float(row["cash"])
                )
                for row in rows
            ]
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_all(self) -> List[Portfolio]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_portafolio, id_cliente, nombre_portafolio, cash FROM portafolio"
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                Portfolio(
                    portfolio_id=row["id_portafolio"],
                    user_id=row["id_cliente"],
                    name=row["nombre_portafolio"],
                    cash_balance=float(row["cash"])
                )
                for row in rows
            ]
        finally:
            cursor.close()
            self.close_connection(conn)

    def update_cash(self, id_portafolio: int, cash: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = "UPDATE portafolio SET cash = %s WHERE id_portafolio = %s"
            cursor.execute(query, (cash, id_portafolio))
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)
