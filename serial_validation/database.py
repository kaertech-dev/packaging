# PACKAGING/serial_validation/database.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def validate_serial_number(serial_num, db_config):
    """Validate serial number and check all process completion status"""
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Get serial number, PO number, and all status columns
            query = """
                SELECT serial_num, po_num, 
                       assembly1, overmould, vi1, lasermarking1, 
                       assembly2, soldering2, vi2, assembly3, 
                       assembly4, vi3, finaltest, assembly5, 
                       packing, lasermarking2, fvi
                FROM faceware_main 
                WHERE serial_num = %s
            """
            cursor.execute(query, (serial_num,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                connection.close()
                return {"success": False, "message": "❌ Serial number not found in database"}
            
            # List of process columns to check (in order)
            process_columns = [
                'assembly1', 'overmould', 'vi1', 'lasermarking1', 
                'assembly2', 'soldering2', 'vi2', 'assembly3', 
                'assembly4', 'vi3', 'finaltest', 'assembly5', 
                'packing', 'lasermarking2', 'fvi'
            ]
            
            # Check status for each process column
            incomplete_processes = []
            for process in process_columns:
                if result.get(process) != 1:
                    incomplete_processes.append(process.upper())
            
            cursor.close()
            connection.close()
            
            if incomplete_processes:
                return {
                    "success": False,
                    "message": f"⚠️ Process incomplete. Complete these stages first:\n{', '.join(incomplete_processes)}",
                    "incomplete_processes": incomplete_processes
                }
            
            return {
                "success": True,
                "data": result,
                "message": "✅ All processes completed. Ready for packaging."
            }
            
    except Error as e:
        return {"success": False, "message": f"❌ Database connection error: {str(e)}"}


def record_operator_login(serial_num, po_num, operator_name, db_config):
    """Record operator login in faceware_packaging1 table and check if already completed"""
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Check if packaging1 is already completed (status = 1)
            check_query = """
                SELECT status, sku, qty 
                FROM faceware_packaging1 
                WHERE serial_num = %s AND status = 1
            """
            cursor.execute(check_query, (serial_num,))
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Packaging already completed (status = 1)
                cursor.close()
                connection.close()
                return {
                    "success": True, 
                    "already_completed": True,
                    "sku": existing_record.get('sku', '43000166102'),
                    "qty": existing_record.get('qty', '2'),
                    "message": "⚠️ Packaging already completed. Showing reprint option..."
                }
            
            # Get current shift
            current_hour = datetime.now().hour
            if 6 <= current_hour < 14:
                shift = "Day"
            elif 14 <= current_hour < 22:
                shift = "Evening"
            else:
                shift = "Night"
            
            # Insert operator login record (or update if exists with status 0)
            insert_query = """
                INSERT INTO faceware_packaging1 
                (serial_num, po_num, operator_en, shift, date_time, status)
                VALUES (%s, %s, %s, %s, %s, 0)
                ON DUPLICATE KEY UPDATE
                operator_en = VALUES(operator_en),
                shift = VALUES(shift),
                date_time = VALUES(date_time)
            """
            
            date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(insert_query, (serial_num, po_num, operator_name, shift, date_time))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return {
                "success": True, 
                "already_completed": False,
                "message": "✅ Operator login recorded successfully"
            }
            
    except Error as e:
        return {
            "success": False, 
            "already_completed": False,
            "message": f"❌ Failed to record login: {str(e)}"
        }