from datetime import datetime
from typing import List, Optional
from app.repositories.base_repository import BaseRepository
from app.data_structures.transaction_node import TransactionNode
from app.data_structures.transaction_ll import TransactionLinkedList

class MovimientoRepository(BaseRepository):
    """
    Repository for the 'movimiento' table in MySQL.
    """
    def save(self, id_portafolio: int, id_activo: int, tipo_mov: str, cantidad: float, precio_por_accion: float, date: datetime, notas: Optional[str] = None) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO movimiento (id_portafolio, id_activo, tipo_mov, cantidad, precio_por_accion, notas, fecha_transaccion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                id_portafolio,
                id_activo,
                tipo_mov,
                cantidad,
                precio_por_accion,
                notas,
                date
            ))
            conn.commit()
            
            cursor.execute("SELECT LAST_INSERT_ID()")
            res = cursor.fetchone()
            if res:
                return res[0]
            raise ValueError("Could not retrieve id_movimiento after save.")
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_all_by_portafolio(self, id_portafolio: int) -> TransactionLinkedList:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT m.id_movimiento, a.ticker, m.tipo_mov, m.cantidad, m.precio_por_accion, m.fecha_transaccion
                FROM movimiento m
                JOIN activo a ON m.id_activo = a.id_activo
                WHERE m.id_portafolio = %s
                ORDER BY m.fecha_transaccion ASC, m.id_movimiento ASC
            """
            cursor.execute(query, (id_portafolio,))
            rows = cursor.fetchall()
            
            ll = TransactionLinkedList()
            for row in rows:
                node = TransactionNode(
                    ticker=row["ticker"],
                    transaction_type=row["tipo_mov"],
                    shares=float(row["cantidad"]),
                    price=float(row["precio_por_accion"]),
                    date=row["fecha_transaccion"]
                )
                # Store the movement ID dynamically on the node so we can track it
                node.id_movimiento = row["id_movimiento"]
                ll.append(node)
            return ll
        finally:
            cursor.close()
            self.close_connection(conn)

    def delete_latest(self, id_portafolio: int) -> Optional[int]:
        """
        Deletes the latest transaction for the given portfolio.
        Returns the id of the deleted movement or None.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Find the latest movement
            query_find = """
                SELECT id_movimiento 
                FROM movimiento 
                WHERE id_portafolio = %s 
                ORDER BY fecha_transaccion DESC, id_movimiento DESC 
                LIMIT 1
            """
            cursor.execute(query_find, (id_portafolio,))
            res = cursor.fetchone()
            if not res:
                return None
            id_mov = res[0]
            
            # Delete it
            query_delete = "DELETE FROM movimiento WHERE id_movimiento = %s"
            cursor.execute(query_delete, (id_mov,))
            conn.commit()
            return id_mov
        finally:
            cursor.close()
            self.close_connection(conn)
