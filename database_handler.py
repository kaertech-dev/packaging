# PACKAGING/database_handler.py
import pymysql
from datetime import datetime
from tkinter import messagebox

class DatabaseHandler:
    def __init__(self):
        self.config = {
            'host': '192.168.1.38',
            'user': 'labeling',
            'password': 'labeling',
            'database': 'ledtech'
        }

    def get_batch_and_po(self, serial_num):
        """Fetch batch_code and po_num from faceware_assembly1 if serial exists."""
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor()
            cursor.execute("SELECT batch_code, po_num FROM faceware_assembly1 WHERE serial_num = %s", (serial_num,))
            result = cursor.fetchone()
            cursor.close()
            db.close()
            if result:
                return result[0], result[1]
            else:
                return None, None
        except pymysql.Error as err:
            print(f"[DB ERROR] {err}")
            return None, None

class insertDatabaseHandler:
    def __init__(self):
        self.config = {
            'host': '192.168.1.38',
            'user': 'labeling',
            'password': 'labeling',
            'database': 'ledtech'
        }

    def record_operator_activity(self, operator, shift, serial_num, batch_code, po_num, 
                                 ship_mode, innerbox, outerbox, pallet_num):
        """Insert operator data with box counting information.
           Checks if serial_num passed all production stations before packaging.
        """
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor(pymysql.cursors.DictCursor)

            # ✅ Step 1: Verify serial exists in faceware_main
            cursor.execute("SELECT * FROM faceware_main WHERE serial_num = %s", (serial_num,))
            main_data = cursor.fetchone()

            if not main_data:
                messagebox.showwarning("Invalid Serial", f"❌ Serial '{serial_num}' not found in faceware_main.")
                print(f"[DB] Serial {serial_num} not found in faceware_main. Skipping insert.")
                cursor.close()
                db.close()
                return False

            # ✅ Step 2: Verify that all required stations have status = 1
            required_stations = [
                "assembly1", "lasermarking1",
                "assembly2", "soldering2", "vi2",
                "assembly4", "vi3", "finaltest",
                "packing", "lasermarking2", "fvi"
            ]

            incomplete_stations = [
                s for s in required_stations
                if s not in main_data or main_data[s] != 1
            ]

            if incomplete_stations:
                first_incomplete = incomplete_stations[0]
                messagebox.showwarning(
                    "Incomplete Process",
                    f"⚠️ Serial '{serial_num}' cannot proceed to packaging.\n"
                    f"Please complete '{first_incomplete.upper()}' station first."
                )
                print(f"[DB] Serial {serial_num} blocked at {first_incomplete}. Status check failed.")
                cursor.close()
                db.close()
                return False

            # ✅ Step 3: Get batch_code & PO if not provided
            if not batch_code or not po_num:
                cursor.execute("SELECT batch_code, po_num FROM faceware_assembly1 WHERE serial_num = %s", (serial_num,))
                assembly_data = cursor.fetchone()
                if assembly_data:
                    batch_code, po_num = assembly_data["batch_code"], assembly_data["po_num"]
                else:
                    messagebox.showwarning("Missing Data", f"⚠️ Serial '{serial_num}' not found in assembly1 table.")
                    cursor.close()
                    db.close()
                    return False

            # ✅ Step 4: Prevent duplicate packaging entries
            check_query = """
                SELECT COUNT(*) AS cnt FROM faceware_packaging 
                WHERE serial_num = %s AND po_num = %s AND batch_code = %s
            """
            cursor.execute(check_query, (serial_num, po_num, batch_code))
            if cursor.fetchone()["cnt"] > 0:
                messagebox.showinfo("Duplicate Detected", f"⚠️ Serial '{serial_num}' already recorded in packaging.")
                print(f"[DB] Duplicate detected → Serial {serial_num} already exists. Skipping insert.")
                cursor.close()
                db.close()
                return False

            # ✅ Step 5: Insert new packaging record
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            insert_query = """
                INSERT INTO faceware_packaging 
                (serial_num, po_num, operator_en, shift, date_time, sku, batch_code, 
                 ship_mode, innerbox, outerbox, pallet_num)
                VALUES (%s, %s, %s, %s, %s, 43000166102, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                serial_num, po_num, operator, shift, now,
                batch_code, ship_mode, innerbox, outerbox, pallet_num
            ))
            db.commit()

            print(f"[DB] ✅ Recorded: Serial {serial_num} | "
                  f"Innerbox {innerbox} | Outerbox {outerbox} | Pallet {pallet_num}")

            cursor.close()
            db.close()
            return True

        except pymysql.Error as err:
            print(f"[DB ERROR] {err}")
            messagebox.showerror("Database Error", f"⚠️ Database error occurred:\n{err}")
            return False

    def update_packaging_status(self, serial_num, po_num, batch_code):
        """Update faceware_main.packaging = 1 and faceware_packaging.status = 1 
           after successful label printing.
        """
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor()

            # ✅ Update faceware_main: Set packaging = 1
            update_main_query = """
                UPDATE faceware_main 
                SET packaging = 1 
                WHERE serial_num = %s
            """
            cursor.execute(update_main_query, (serial_num,))
            
            # ✅ Update faceware_packaging: Set status = 1
            update_packaging_query = """
                UPDATE faceware_packaging 
                SET status = 1 
                WHERE serial_num = %s AND po_num = %s AND batch_code = %s
            """
            cursor.execute(update_packaging_query, (serial_num, po_num, batch_code))
            
            db.commit()
            
            rows_affected_main = cursor.rowcount
            print(f"[DB] ✅ Updated packaging status: "
                  f"faceware_main.packaging=1, faceware_packaging.status=1 "
                  f"for serial {serial_num}")

            cursor.close()
            db.close()
            
            return True

        except pymysql.Error as err:
            print(f"[DB ERROR] Failed to update packaging status: {err}")
            return False
    def check_existing_packaging(self, serial_num, po_num, batch_code):
        """Check if serial_num already exists in faceware_packaging.
           Returns packaging data if found, None otherwise.
        """
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor(pymysql.cursors.DictCursor)
            
            query = """
                SELECT serial_num, batch_code, innerbox, outerbox, pallet_num, operator_en, date_time
                FROM faceware_packaging 
                WHERE serial_num = %s AND po_num = %s AND batch_code = %s
                LIMIT 1
            """
            cursor.execute(query, (serial_num, po_num, batch_code))
            result = cursor.fetchone()
            
            cursor.close()
            db.close()
            
            if result:
                print(f"[DB] ✅ Found existing packaging record for serial {serial_num}")
                return result
            else:
                return None
                
        except pymysql.Error as err:
            print(f"[DB ERROR] Failed to check existing packaging: {err}")
            return None

    def get_batch_unit_count(self, batch_code, po_num):
        """Count how many units have already been packaged for this batch code.
           This prevents duplicate innerbox/outerbox/pallet numbering.
           Returns: integer count of packaged units for this batch
        """
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor()
            
            query = """
                SELECT COUNT(*) as total_units
                FROM faceware_packaging 
                WHERE batch_code = %s AND po_num = %s
            """
            cursor.execute(query, (batch_code, po_num))
            result = cursor.fetchone()
            
            cursor.close()
            db.close()
            
            if result:
                count = result[0]
                print(f"[DB] ✅ Batch '{batch_code}' has {count} units already packaged")
                return count
            else:
                return 0
                
        except pymysql.Error as err:
            print(f"[DB ERROR] Failed to count batch units: {err}")
            return 0  # Return 0 on error to prevent blocking operations
    
    def get_total_packaged_units(self):
        """Get total count of all units in faceware_packaging table.
        Returns: integer count of all packaged units
        """
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor()
            
            query = """
                SELECT COUNT(*) as total_units
                FROM faceware_packaging
            """
            cursor.execute(query)
            result = cursor.fetchone()
            
            cursor.close()
            db.close()
            
            if result:
                count = result[0]
                print(f"[DB] ✅ Total packaged units: {count}")
                return count
            else:
                return 0
                
        except pymysql.Error as err:
            print(f"[DB ERROR] Failed to count total units: {err}")
            return 0  # Return 0 on error
    
    def get_pallet_unit_count(self, pallet_num, po_num):
        """Count how many units are already in a specific pallet number.
        Returns: integer count of units in this pallet
        """
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor()
            
            query = """
                SELECT COUNT(*) as total_units
                FROM faceware_packaging 
                WHERE pallet_num = %s AND po_num = %s
            """
            cursor.execute(query, (pallet_num, po_num))
            result = cursor.fetchone()
            
            cursor.close()
            db.close()
            
            if result:
                count = result[0]
                print(f"[DB] ✅ Pallet {pallet_num} has {count} units in database")
                return count
            else:
                return 0
                
        except pymysql.Error as err:
            print(f"[DB ERROR] Failed to count pallet units: {err}")
            return 0 # Return 0 on error
    # ...existing code...

    def get_unfinished_batches(self):
        """Return list of unfinished batches with simple stats."""
        try:
            query = """
            SELECT batch_code, po_num, pallet_num, COUNT(*) AS unit_count
            FROM operator_activity
            WHERE packaging = 0
            GROUP BY batch_code, po_num, pallet_num
            ORDER BY batch_code DESC;
            """
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return [{'batch_code': r[0], 'po_num': r[1], 'pallet_num': r[2], 'unit_count': r[3]} for r in rows]
        except Exception as e:
            print("get_unfinished_batches error:", e)
            return []

    def get_batch_info(self, batch_code):
        """Return aggregated info for a batch_code."""
        try:
            query = """
            SELECT batch_code, po_num, pallet_num, COUNT(*) AS unit_count
            FROM operator_activity
            WHERE batch_code = %s
            GROUP BY batch_code, po_num, pallet_num;
            """
            self.cursor.execute(query, (batch_code,))
            r = self.cursor.fetchone()
            if not r:
                return None
            return {'batch_code': r[0], 'po_num': r[1], 'pallet_num': r[2], 'unit_count': r[3]}
        except Exception as e:
            print("get_batch_info error:", e)
            return None

    # Add this method to the insertDatabaseHandler class in database_handler.py

    def get_unfinished_batches(self):
        """Return list of unfinished batches with their statistics.
        Returns batches that haven't completed their pallet capacity.
        """
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor(pymysql.cursors.DictCursor)
            
            # Query to get batch information grouped by batch_code and pallet_num
            query = """
                SELECT 
                    batch_code,
                    po_num,
                    pallet_num,
                    COUNT(*) as unit_count,
                    MAX(date_time) as last_updated
                FROM faceware_packaging
                GROUP BY batch_code, po_num, pallet_num
                ORDER BY last_updated DESC, batch_code DESC
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            cursor.close()
            db.close()
            
            if results:
                print(f"[DB] Found {len(results)} batch/pallet combinations")
                return results
            else:
                print("[DB] No unfinished batches found")
                return []
                
        except pymysql.Error as err:
            print(f"[DB ERROR] get_unfinished_batches: {err}")
            return []