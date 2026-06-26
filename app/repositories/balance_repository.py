from typing import Optional, List
from app.repositories.base_repository import BaseRepository
from app.models.domain import BalanceSheet

class BalanceRepository(BaseRepository):
    """
    Repository for the 'balance_sheet' table.
    """
    def save(self, stmt: BalanceSheet):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO balance_sheet (id_activo, periodo, fecha_reporte, total_assets, total_liabilities, total_equity, total_debt, cash_equivalents, current_assets, current_liabilities)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    fecha_reporte = VALUES(fecha_reporte),
                    total_assets = VALUES(total_assets),
                    total_liabilities = VALUES(total_liabilities),
                    total_equity = VALUES(total_equity),
                    total_debt = VALUES(total_debt),
                    cash_equivalents = VALUES(cash_equivalents),
                    current_assets = VALUES(current_assets),
                    current_liabilities = VALUES(current_liabilities)
            """
            cursor.execute(query, (
                stmt.id_activo,
                stmt.periodo,
                stmt.fecha_reporte,
                stmt.total_assets,
                stmt.total_liabilities,
                stmt.total_equity,
                stmt.total_debt,
                stmt.cash_equivalents,
                stmt.current_assets,
                stmt.current_liabilities
            ))
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_statement(self, id_activo: int, periodo: str) -> Optional[BalanceSheet]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM balance_sheet WHERE id_activo = %s AND periodo = %s"
            cursor.execute(query, (id_activo, periodo))
            row = cursor.fetchone()
            if row:
                return self._map_row(row)
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_all(self, id_activo: int) -> List[BalanceSheet]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM balance_sheet WHERE id_activo = %s ORDER BY fecha_reporte DESC"
            cursor.execute(query, (id_activo,))
            rows = cursor.fetchall()
            return [self._map_row(r) for r in rows]
        finally:
            cursor.close()
            self.close_connection(conn)

    def _map_row(self, row: dict) -> BalanceSheet:
        return BalanceSheet(
            id_balance=row["id_balance"],
            id_activo=row["id_activo"],
            periodo=row["periodo"],
            fecha_reporte=row["fecha_reporte"],
            total_assets=float(row["total_assets"]) if row["total_assets"] else None,
            total_liabilities=float(row["total_liabilities"]) if row["total_liabilities"] else None,
            total_equity=float(row["total_equity"]) if row["total_equity"] else None,
            total_debt=float(row["total_debt"]) if row["total_debt"] else None,
            cash_equivalents=float(row["cash_equivalents"]) if row["cash_equivalents"] else None,
            current_assets=float(row["current_assets"]) if row["current_assets"] else None,
            current_liabilities=float(row["current_liabilities"]) if row["current_liabilities"] else None
        )
