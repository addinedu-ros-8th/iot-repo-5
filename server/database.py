import mysql.connector

class pickup_database:
    def __init__(self, host, user, password, database):
        try:
            self.conn = mysql.connector.connect(
                host = host,
                user = user,
                password = password,
                database = database
            )

            if self.conn.is_connected():
                print("success connect...")
        except Exception as e:
            print("failed connect...", e)

    def execute_query(self, query, param=None):
        if not self.conn.is_connected():
            print("not connected db...")
            return
        
        cursor = self.conn.cursor()
        cursor.execute(query, param)

        id = cursor.lastrowid

        cursor.close()

        return id
    
    def execute_many(self, query, param=None):
        if not self.conn.is_connected():
            print("not connected db...")
            return
        
        cursor = self.conn.cursor(prepared=True)
        cursor.executemany(query, param)
        cursor.close()

        return True

    def fetch_all(self, query, params=None):
        if not self.conn.is_connected():
            print("not connected db...")
            return
        
        cursor = self.conn.cursor(buffered=True)
        try:
            cursor.execute(query, params)

            result = cursor.fetchall()

            return result
        except Exception as e:
            print("failed fetch...", e)
            return
        finally:
            cursor.close()

    def fetch_one(self, query, params=None):
        if not self.conn.is_connected():
            print("not connected db...")
            return
        cursor = self.conn.cursor(buffered=True)
        try:
            cursor.execute(query, params)
            
            result = cursor.fetchone()

            return result
        except Exception as e:
            print("failed fetch...", e)
            return None
        finally:
            cursor.close()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def dispose(self):
        self.conn.close()
        print("disconnect db...")