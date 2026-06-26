from typing import Optional, List
from app.repositories.base_repository import BaseRepository
from app.models.domain import CashFlow

class CashFlowRepository(BaseRepository):
    """
    Repository for the 'cash_flow' table.
    """
    def save(self, stmt: CashFlow):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO cash_flow (id_activo, periodo, fecha_reporte, operating_cf, investing_cf, financing_cf, free_cash_flow, capex)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    fecha_reporte = VALUES(fecha_reporte),
                    operating_cf = VALUES(operating_cf),
                    investing_cf = VALUES(investing_cf),
                    financing_cf = VALUES(financing_cf),
                    free_cash_flow = VALUES(free_cash_flow),
                    capex = VALUES(capex)
            """
            cursor.execute(query, (
                stmt.id_activo,
                stmt.periodo,
                stmt.fecha_reporte,
                stmt.operating_cf,
                stmt.investing_cf,
                stmt.financing_cf,
                stmt.free_cash_flow,
                stmt.capex
            ))
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_statement(self, id_activo: int, periodo: str) -> Optional[CashFlow]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM cash_flow WHERE id_activo = %s AND periodo = %s"
            cursor.execute(query, (id_activo, periodo))
            row = cursor.fetchone()
            if row:
                return self._map_row(row)
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_all(self, id_activo: int) -> List[CashFlow]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM cash_flow WHERE id_activo = %s ORDER BY fecha_reporte DESC"
            cursor.execute(query, (id_activo,))
            rows = cursor.fetchall()
            return [self._map_row(r) for r in rows]
        finally:
            cursor.close()
            self.close_connection(conn)

    def _map_row(self, row: dict) -> CashFlow:
        return CashFlow(
            id_cashflow=row["id_cashflow"],
            id_activo=row["id_activo"],
            periodo=row["periodo"],
            fecha_reporte=row["fecha_reporte"],
            operating_cf=float(row["operating_cf"]) if row["operating_cf"] else None,
            investing_cf=float(row["investing_cf"]) if row["investing_cf"] else None,
            financing_cf=float(row["financing_cf"]) if row["financing_cf"] else None,
            free_cash_flow=float(row["free_cash_flow"]) if row["free_cash_flow"] else None,
            capex=float(row["capex"]) if row["capex"] else None
        )
