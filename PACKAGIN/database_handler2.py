# PACKAGING/database_handler2.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def record_packaging_data(serial_num, sku, qty, db_config):
    """
    Record SKU and QTY in faceware_packaging2 and update status in both tables
    
    Args:
        serial_num: Serial number (or LOT/PO number based on your usage)
        sku: SKU label value
        qty: Quantity
        db_config: Database configuration
    
    Returns:
        dict: {"success": bool, "message": str, "already_submitted": bool (optional)}
    """
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Check if packaging2 is already submitted (status = 1)
            check_query = """
                SELECT status, sku, qty 
                FROM faceware_packaging2 
                WHERE serial_num = %s
            """
            cursor.execute(check_query, (serial_num,))
            existing_record = cursor.fetchone()
            
            if existing_record:
                if existing_record['status'] == 1:
                    # Already submitted
                    cursor.close()
                    connection.close()
                    return {
                        "success": False,
                        "already_submitted": True,
                        "existing_sku": existing_record['sku'],
                        "existing_qty": existing_record['qty'],
                        "message": "⚠️ Packaging 2 already submitted!"
                    }
            
            # Update faceware_packaging2 with SKU and QTY, and set status = 1
            update_packaging_query = """
                UPDATE faceware_packaging2 
                SET sku = %s, qty = %s, status = 1
                WHERE serial_num = %s
            """
            cursor.execute(update_packaging_query, (sku, qty, serial_num))
            
            # Update faceware_main packaging2 status = 1
            update_main_query = """
                UPDATE faceware_main 
                SET packaging2 = 1
                WHERE serial_num = %s
            """
            cursor.execute(update_main_query, (serial_num,))
            
            connection.commit()
            
            if cursor.rowcount > 0:
                cursor.close()
                connection.close()
                return {
                    "success": True, 
                    "message": "✅ Packaging 2 data recorded successfully!"
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