from typing import Optional, List
from app.repositories.base_repository import BaseRepository
from app.models.domain import IncomeStatement

class IncomeRepository(BaseRepository):
    """
    Repository for the 'income_statement' table.
    """
    def save(self, stmt: IncomeStatement):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO income_statement (id_activo, periodo, fecha_reporte, revenue, cost_of_revenue, gross_profit, operating_expenses, operating_income, net_income, ebitda, shares_outstanding, interest_expense, tax_expense)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    fecha_reporte = VALUES(fecha_reporte),
                    revenue = VALUES(revenue),
                    cost_of_revenue = VALUES(cost_of_revenue),
                    gross_profit = VALUES(gross_profit),
                    operating_expenses = VALUES(operating_expenses),
                    operating_income = VALUES(operating_income),
                    net_income = VALUES(net_income),
                    ebitda = VALUES(ebitda),
                    shares_outstanding = VALUES(shares_outstanding),
                    interest_expense = VALUES(interest_expense),
                    tax_expense = VALUES(tax_expense)
            """
            cursor.execute(query, (
                stmt.id_activo,
                stmt.periodo,
                stmt.fecha_reporte,
                stmt.revenue,
                stmt.cost_of_revenue,
                stmt.gross_profit,
                stmt.operating_expenses,
                stmt.operating_income,
                stmt.net_income,
                stmt.ebitda,
                stmt.shares_outstanding,
                stmt.interest_expense,
                stmt.tax_expense
            ))
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_statement(self, id_activo: int, periodo: str) -> Optional[IncomeStatement]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM income_statement WHERE id_activo = %s AND periodo = %s"
            cursor.execute(query, (id_activo, periodo))
            row = cursor.fetchone()
            if row:
                return self._map_row(row)
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_all(self, id_activo: int) -> List[IncomeStatement]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM income_statement WHERE id_activo = %s ORDER BY fecha_reporte DESC"
            cursor.execute(query, (id_activo,))
            rows = cursor.fetchall()
            return [self._map_row(r) for r in rows]
        finally:
            cursor.close()
            self.close_connection(conn)

    def _map_row(self, row: dict) -> IncomeStatement:
        return IncomeStatement(
            id_statement=row["id_statement"],
            id_activo=row["id_activo"],
            periodo=row["periodo"],
            fecha_reporte=row["fecha_reporte"],
            revenue=float(row["revenue"]) if row["revenue"] else None,
            cost_of_revenue=float(row["cost_of_revenue"]) if row["cost_of_revenue"] else None,
            gross_profit=float(row["gross_profit"]) if row["gross_profit"] else None,
            operating_expenses=float(row["operating_expenses"]) if row["operating_expenses"] else None,
            operating_income=float(row["operating_income"]) if row["operating_income"] else None,
            net_income=float(row["net_income"]) if row["net_income"] else None,
            ebitda=float(row["ebitda"]) if row["ebitda"] else None,
            shares_outstanding=row["shares_outstanding"],
            interest_expense=float(row["interest_expense"]) if row["interest_expense"] else None,
            tax_expense=float(row["tax_expense"]) if row["tax_expense"] else None
        )
