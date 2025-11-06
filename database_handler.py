# PACKAGING/database_handler.py
import mysql.connector
from datetime import datetime
from tkinter import messagebox

class DatabaseHandler:
    def __init__(self):
        self.config = {
            'host': '192.168.1.38',
            'user': 'testing',
            'password': 'testing',
            'database': 'ledtech'
        }

    def get_batch_and_po(self, serial_num):
        """Fetch batch_code and po_num from faceware_assembly1 if serial exists."""
        try:
            db = mysql.connector.connect(**self.config)
            cursor = db.cursor()
            cursor.execute("SELECT batch_code, po_num FROM faceware_assembly1 WHERE serial_num = %s", (serial_num,))
            result = cursor.fetchone()
            cursor.close()
            db.close()
            if result:
                return result[0], result[1]
            else:
                return None, None
        except mysql.connector.Error as err:
            print(f"[DB ERROR] {err}")
            return None, None

class insertDatabaseHandler:
    def __init__(self):
        self.config = {
            'host': '192.168.1.38',
            'user': 'testing',
            'password': 'testing',
            'database': 'ledtech'
        }

    def record_operator_activity(self, operator, shift, serial_num, batch_code, po_num, 
                                 ship_mode, innerbox, outerbox, pallet_num):
        """Insert operator data with box counting information.
           Checks if serial_num passed all production stations before packaging.
        """
        try:
            db = mysql.connector.connect(**self.config)
            cursor = db.cursor(dictionary=True)

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
                SELECT COUNT(*) AS cnt FROM faceware_packagingryan 
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
                INSERT INTO faceware_packagingryan
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

        except mysql.connector.Error as err:
            print(f"[DB ERROR] {err}")
            messagebox.showerror("Database Error", f"⚠️ Database error occurred:\n{err}")
            return False

    def update_packaging_status(self, serial_num, po_num, batch_code):
        """Update faceware_main.packaging = 1 and faceware_packagingryan.status = 1 
           after successful label printing.
        """
        try:
            db = mysql.connector.connect(**self.config)
            cursor = db.cursor()

            # ✅ Update faceware_main: Set packaging = 1
            update_main_query = """
                UPDATE faceware_main 
                SET packaging = 1 
                WHERE serial_num = %s
            """
            cursor.execute(update_main_query, (serial_num,))

            # ✅ Update faceware_packagingryan: Set status = 1
            update_packaging_query = """
                UPDATE faceware_packagingryan
                SET status = 1
                WHERE serial_num = %s AND po_num = %s AND batch_code = %s
            """
            cursor.execute(update_packaging_query, (serial_num, po_num, batch_code))
            
            db.commit()
            
            rows_affected_main = cursor.rowcount
            print(f"[DB] ✅ Updated packaging status: "
                  f"faceware_main.packaging=1, faceware_packagingryan.status=1 "
                  f"for serial {serial_num}")

            cursor.close()
            db.close()
            
            return True

        except mysql.connector.Error as err:
            print(f"[DB ERROR] Failed to update packaging status: {err}")
            return False

    
    def check_existing_packaging(self, serial_num, po_num, batch_code):
        """Check if serial_num already exists in faceware_packagingryan.
           Returns packaging data if found, None otherwise.
        """
    def check_existing_packaging(self, serial_num, po_num, batch_code):
        """Check if serial_num already exists in faceware_packaging.

           Returns packaging data if found, None otherwise.
        """
        try:
            db = mysql.connector.connect(**self.config)
            cursor = db.cursor(dictionary=True)
            
            query = """
                SELECT serial_num, batch_code, innerbox, outerbox, pallet_num, operator_en, date_time
                FROM faceware_packagingryan
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
                
        except mysql.connector.Error as err:
            print(f"[DB ERROR] Failed to check existing packaging: {err}")
            return None

    def get_batch_unit_count(self, batch_code, po_num):
        """Count how many units have already been packaged for this batch code.
           This prevents duplicate innerbox/outerbox/pallet numbering.
           Returns: integer count of packaged units for this batch
        """
        try:
            db = mysql.connector.connect(**self.config)
            cursor = db.cursor()
            
            query = """
                SELECT COUNT(*) as total_units

                FROM faceware_packagingryan

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
                
        except mysql.connector.Error as err:
            print(f"[DB ERROR] Failed to count batch units: {err}")
            return 0  # Return 0 on error to prevent blocking operations
    
    def get_total_packaged_units(self):
        """Get total count of all units in faceware_packagingryan table.
        Returns: integer count of all packaged units
        """
        try:
            db = mysql.connector.connect(**self.config)
            cursor = db.cursor()
            
            query = """
                SELECT COUNT(*) as total_units
                FROM faceware_packagingryan
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
                
        except mysql.connector.Error as err:
            print(f"[DB ERROR] Failed to count total units: {err}")
            return 0  # Return 0 on error
    
    def get_current_pallet_for_batch(self, batch_code, po_num, total_units_per_pallet):
        """Get the current pallet number for a batch code.
           Returns: (pallet_num, units_in_pallet)
           - pallet_num: Current pallet number for this batch
           - units_in_pallet: Number of units already in the current pallet
        """
        try:
            db = mysql.connector.connect(**self.config)
            cursor = db.cursor(dictionary=True)
            
            # Get the highest pallet number for this batch
            query = """
                SELECT MAX(pallet_num) as max_pallet
                FROM faceware_packagingryan
                WHERE batch_code = %s AND po_num = %s
            """
            cursor.execute(query, (batch_code, po_num))
            result = cursor.fetchone()
            
            if result and result['max_pallet'] is not None:
                current_pallet = result['max_pallet']
                
                # Count units in the current pallet
                count_query = """
                    SELECT COUNT(*) as unit_count
                    FROM faceware_packagingryan
                    WHERE batch_code = %s AND po_num = %s AND pallet_num = %s
                """
                cursor.execute(count_query, (batch_code, po_num, current_pallet))
                count_result = cursor.fetchone()
                units_in_pallet = count_result['unit_count'] if count_result else 0
                
                # Check if current pallet is full
                if units_in_pallet >= total_units_per_pallet:
                    # Current pallet is full, move to next pallet
                    current_pallet += 1
                    units_in_pallet = 0
                    print(f"[DB] ✅ Batch '{batch_code}' pallet {current_pallet - 1} is full. Moving to pallet {current_pallet}")
                else:
                    print(f"[DB] ✅ Batch '{batch_code}' continuing on pallet {current_pallet} ({units_in_pallet} units)")
                
                cursor.close()
                db.close()
                return current_pallet, units_in_pallet
            else:
                # No existing pallets for this batch, start with pallet 1
                cursor.close()
                db.close()
                print(f"[DB] ✅ Batch '{batch_code}' starting new - Pallet 1")
                return 1, 0
                
        except mysql.connector.Error as err:
            print(f"[DB ERROR] Failed to get current pallet: {err}")
            return 1, 0  # Default to pallet 1 on error
    
    def get_pallet_unit_count(self, pallet_num, po_num, batch_code=None):
        """Count how many units are already in a specific pallet number.
        Returns: integer count of units in this pallet
        """
        try:
            db = mysql.connector.connect(**self.config)
            cursor = db.cursor()
            
            if batch_code:
                query = """
                    SELECT COUNT(*) as total_units
                    FROM faceware_packagingryan
                    WHERE pallet_num = %s AND po_num = %s AND batch_code = %s
                """
                cursor.execute(query, (pallet_num, po_num, batch_code))
            else:
                query = """
                    SELECT COUNT(*) as total_units
                    FROM faceware_packagingryan
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
                
        except mysql.connector.Error as err:
            print(f"[DB ERROR] Failed to count pallet units: {err}")
            return 0  # Return 0 on error
            return 0  # Return 0 on error to prevent blocking operations

