from typing import Optional
from app.repositories.base_repository import BaseRepository
from app.models.domain import BondDetails

class BondRepository(BaseRepository):
    """
    Repository for the 'bond' table.
    """
    def save(self, details: BondDetails):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO bond (id_activo, fecha_maduracion, tasa_cupon, frecuencia_pago, valor_nominal, calificacion, emisor)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    fecha_maduracion = VALUES(fecha_maduracion),
                    tasa_cupon = VALUES(tasa_cupon),
                    frecuencia_pago = VALUES(frecuencia_pago),
                    valor_nominal = VALUES(valor_nominal),
                    calificacion = VALUES(calificacion),
                    emisor = VALUES(emisor)
            """
            cursor.execute(query, (
                details.id_activo,
                details.fecha_maduracion,
                details.tasa_cupon,
                details.frecuencia_pago,
                details.valor_nominal,
                details.calificacion,
                details.emisor
            ))
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_by_id(self, id_activo: int) -> Optional[BondDetails]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_activo, fecha_maduracion, tasa_cupon, frecuencia_pago, valor_nominal, calificacion, emisor FROM bond WHERE id_activo = %s"
            cursor.execute(query, (id_activo,))
            row = cursor.fetchone()
            if row:
                return BondDetails(
                    id_activo=row["id_activo"],
                    fecha_maduracion=row["fecha_maduracion"],
                    tasa_cupon=float(row["tasa_cupon"]) if row["tasa_cupon"] else None,
                    frecuencia_pago=row["frecuencia_pago"],
                    valor_nominal=float(row["valor_nominal"]) if row["valor_nominal"] else None,
                    calificacion=row["calificacion"],
                    emisor=row["emisor"]
                )
            return None
        finally:
            cursor.close()
            self.close_connection(conn)
