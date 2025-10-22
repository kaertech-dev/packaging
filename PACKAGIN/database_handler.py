# PACKAGING/database_handler.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def record_packaging_data(lot, serial_num, sku, qty, po_num, db_config):
    """
    Record SKU and QTY in faceware_packaging1 and update status in both tables
    
    Args:
        serial_num: Serial number
        sku: SKU label value
        qty: Quantity
        db_config: Database configuration
    
    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Update faceware_packaging1 with SKU and QTY, and set status = 1
            update_packaging_query = """
                UPDATE faceware_packaging1 
                SET sku = %s, qty = %s, status = 1
                WHERE serial_num = %s
            """
            cursor.execute(update_packaging_query, (sku, qty, serial_num))
            
            # Update faceware_main packaging status = 1
            update_main_query = """
                UPDATE faceware_main 
                SET packaging1 = 1
                WHERE serial_num = %s
            """
            cursor.execute(update_main_query, (serial_num,))
            
            connection.commit()
            
            if cursor.rowcount > 0:
                cursor.close()
                connection.close()
                return {
                    "success": True, 
                    "message": "✅ Packaging data recorded successfully!"
                }
            else:
                cursor.close()
                connection.close()
                return {
                    "success": False, 
                    "message": "❌ No records updated. Serial number may not exist."
                }
            
    except Error as e:
        return {
            "success": False, 
            "message": f"❌ Database error: {str(e)}"
        }
