from typing import Optional, List
from app.repositories.base_repository import BaseRepository
from app.models.domain import FinancialRatios

class RatiosRepository(BaseRepository):
    """
    Repository for the 'ratios_financieros' table.
    """
    def save(self, ratios: FinancialRatios):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO ratios_financieros (id_activo, periodo, fecha_reporte, roe, roa, roic, ev_ebitda, gross_margin, operating_margin, net_margin, quick_ratio, current_ratio, debt_equity, icr, asset_turnover, eps, eps_growth, revenue_growth, fcf_yield)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    fecha_reporte = VALUES(fecha_reporte),
                    roe = VALUES(roe),
                    roa = VALUES(roa),
                    roic = VALUES(roic),
                    ev_ebitda = VALUES(ev_ebitda),
                    gross_margin = VALUES(gross_margin),
                    operating_margin = VALUES(operating_margin),
                    net_margin = VALUES(net_margin),
                    quick_ratio = VALUES(quick_ratio),
                    current_ratio = VALUES(current_ratio),
                    debt_equity = VALUES(debt_equity),
                    icr = VALUES(icr),
                    asset_turnover = VALUES(asset_turnover),
                    eps = VALUES(eps),
                    eps_growth = VALUES(eps_growth),
                    revenue_growth = VALUES(revenue_growth),
                    fcf_yield = VALUES(fcf_yield)
            """
            cursor.execute(query, (
                ratios.id_activo,
                ratios.periodo,
                ratios.fecha_reporte,
                ratios.roe,
                ratios.roa,
                ratios.roic,
                ratios.ev_ebitda,
                ratios.gross_margin,
                ratios.operating_margin,
                ratios.net_margin,
                ratios.quick_ratio,
                ratios.current_ratio,
                ratios.debt_equity,
                ratios.icr,
                ratios.asset_turnover,
                ratios.eps,
                ratios.eps_growth,
                ratios.revenue_growth,
                ratios.fcf_yield
            ))
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_ratios(self, id_activo: int, periodo: str) -> Optional[FinancialRatios]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM ratios_financieros WHERE id_activo = %s AND periodo = %s"
            cursor.execute(query, (id_activo, periodo))
            row = cursor.fetchone()
            if row:
                return self._map_row(row)
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_all(self, id_activo: int) -> List[FinancialRatios]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM ratios_financieros WHERE id_activo = %s ORDER BY fecha_reporte DESC"
            cursor.execute(query, (id_activo,))
            rows = cursor.fetchall()
            return [self._map_row(r) for r in rows]
        finally:
            cursor.close()
            self.close_connection(conn)

    def _map_row(self, row: dict) -> FinancialRatios:
        return FinancialRatios(
            id_ratio=row["id_ratio"],
            id_activo=row["id_activo"],
            periodo=row["periodo"],
            fecha_reporte=row["fecha_reporte"],
            roe=float(row["roe"]) if row["roe"] else None,
            roa=float(row["roa"]) if row["roa"] else None,
            roic=float(row["roic"]) if row["roic"] else None,
            ev_ebitda=float(row["ev_ebitda"]) if row["ev_ebitda"] else None,
            gross_margin=float(row["gross_margin"]) if row["gross_margin"] else None,
            operating_margin=float(row["operating_margin"]) if row["operating_margin"] else None,
            net_margin=float(row["net_margin"]) if row["net_margin"] else None,
            quick_ratio=float(row["quick_ratio"]) if row["quick_ratio"] else None,
            current_ratio=float(row["current_ratio"]) if row["current_ratio"] else None,
            debt_equity=float(row["debt_equity"]) if row["debt_equity"] else None,
            icr=float(row["icr"]) if row["icr"] else None,
            asset_turnover=float(row["asset_turnover"]) if row["asset_turnover"] else None,
            eps=float(row["eps"]) if row["eps"] else None,
            eps_growth=float(row["eps_growth"]) if row["eps_growth"] else None,
            revenue_growth=float(row["revenue_growth"]) if row["revenue_growth"] else None,
            fcf_yield=float(row["fcf_yield"]) if row["fcf_yield"] else None
        )
