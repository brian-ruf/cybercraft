# Database Class
#
# =============================================================================
# Database Handling
# https://www.pythonlore.com/handling-database-errors-and-exceptions-in-sqlalchemy/
# https://stackoverflow.com/questions/2136739/error-handling-in-sqlalchemy
# =============================================================================
# TODO: Evaluate using SQLAlchemy for database handling
# TODO: Handle additional database types beyond sqlite3
# =============================================================================
import sqlite3
from loguru import logger
from . import misc
from . import type_sqlite3
import asyncio

# List of supported databses:
# - sqlite3: SQLite 3
# - Others TBD: PostgreSQL, MS-SQL, MySQL
SUPPORTED={"sqlite3": "SQLite 3"}

CONTENT_COMPRESSION = True # Set to True to compress the file cache
                            # Set to False for debugging or if inspection
                            # of the raw, downloaded content is required

OSCAL_COMMON_TABLES = {}
OSCAL_COMMON_TABLES["filecache"] = {
    "table_name": "filecache", 
    "table_fields": [
        {"name": "uuid"             , "type": "TEXT"   , "attributes": "PRIMARY KEY", "hide": True, "description": "Unique identifier for the file."},
        {"name": "filename"         , "type": "TEXT"   , "label" : "File Name"  , "description": "The name of the file."},
        {"name": "original_location", "type": "TEXT"   , "label" : "Original Location", "description": "The original location of the file."},
        {"name": "mime_type"        , "type": "TEXT"   , "label" : "MIME Type"  , "description": "The MIME type of the file."},
        {"name": "file_type"        , "type": "TEXT"   , "label" : "File Type"  , "description": "The type of file."},
        {"name": "acquired"         , "type": "NUMERIC", "label" : "Acquired"   , "description": "The date and time the file was acquired from the source."},
        {"name": "datatype"         , "type": "TEXT"   , "label" : "Data Type"  , "description": "The original Python data type of the content before it was saved to the database."},
        {"name": "compressed"       , "type": "NUMERIC", "label" : "Compression", "description": "Indicates whether the content was compressed before it was saved to the database."},
        {"name": "content"          , "type": "BLOB"   , "hide": True           , "description": "The content of the file."}
    ],
    "table_indexes": [
        {"name": "oscal_version", "fields": ["oscal_version"]},
        {"name": "file_type"    , "fields": ["file_type"]}
    ]
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Database:
    def __init__(self, type, target):
        """
        Creates a database object and opens the database.
        type: The type of database. Supported types:
           - sqlite3: SQLite3 database on a local file system
        target:
            - For sqlite3 this is the path and filename of the database
            - Otherwise, this is the connection string for the database
        """
        self.target = target # The path and filename of the database
        self.type = type     # The type of database (sqlite3, mysql, etc.)
        self.conn = None     # The database connection object
        self.cursor = None   # The database cursor object
        self.status = False  # True if open and ready for use
        self.last_operation = "" # The last operation performed on the database
        self.last_operation_result = "" # The result of the last operation performed on the database
        self.supported = SUPPORTED  # List of supported database types
        self.has_file_cache = False # Indicates whether the database includes a file cache
        self.open()

    # -------------------------------------------------------------------------
    def __str__(self):
        ret_val = ""
        ret_val += f"Database Type: {self.type}" 
        ret_val += f"Database Target: {self.target}" 
        ret_val += f"Status: {misc.iff(self.status, 'Ready', 'Not Ready')}" 
        return ret_val
    # -------------------------------------------------------------------------
    def __del__(self):
        if self.conn:
            self.conn.close()            

    # -------------------------------------------------------------------------
    def open(self):
        """Executes the correct open function/tasks based on the database type."""

        if self.type == "sqlite3":
            self.conn = type_sqlite3.open_sqlite3(self.target)
        elif self.type in self.supported:
            logger.error(f"Unhandled database type: {self.type}")
        else:
            logger.error(f"Unsupported database type: {self.type}")

    # -------------------------------------------------------------------------
    async def check_for_tables(self, tables):
        """
        Check for the presence of the expected tables in the database.
        """
        # TODO: Check database structure against specified
        #       structure and modify fields as needed.
        status = True
        for key in tables:
            if self.table_exists(key):
                status = status and True
            else:
                table_exists = await self.create_table(tables[key])
                status = status and table_exists

        return status


    # -------------------------------------------------------------------------
    def table_exists(self, name):
        """
        Determines if a table exists in the database
        - name: A string containing the name of the table
        Returns: True if the table exits. False otherwise. 
        """
        try:
            status = False

            statement = f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{name}'"
            # Get the count of tables with the name
            cursor = self.conn.cursor()
            cursor.execute(statement)

            # If the count is 1, then table exists
            status = (cursor.fetchone()[0] == 1) 
            logger.debug(f"Table {name} {misc.iif(status, "exists", "does not exist")}.")

        except sqlite3.IntegrityError:
            logger.error("Integrity Error: This violates the database's integrity rules.")
        except sqlite3.ProgrammingError as pe:
            logger.error(f"Programming Error: {pe}")
        except sqlite3.OperationalError as oe:
            logger.error(f"Operational Error: {oe}")
        except sqlite3.DatabaseError as de:
            logger.error(f"Database Error: {de}")
        except sqlite3.DataError as dte:
            logger.error(f"Data Error: {dte}")
        except sqlite3.InterfaceError as ie:
            logger.error(f"Interface Error: {ie}")
        except sqlite3.InternalError as ine:
            logger.error(f"Internal Error: {ine}")
        except sqlite3.NotSupportedError as nse:
            logger.error(f"Not Supported Error: {nse}")
        except (Exception, BaseException) as error:
            logger.error(f"Unrecognized error checking for table {name} ({type(error).__name__}): {str(error)}")
        return status
    # -------------------------------------------------------------------------
    def record_count(self, table, where_clause):
        """
        Returns the number of records that include a value
        - table: A string containing the name of the table
        - field: the name of a key field in the table
        - where_clause: The ANSI SQL where clause on which to base the count
        Returns: (int) the number of records that match the query
                 (int) 0 if no records found
                 (int) -1 if an error occurs  
        """
        count = -1
        try:

            statement = f"SELECT count(*) FROM {table} WHERE {where_clause}"
            # Get the count of tables with the name
            cursor = self.conn.cursor()
            cursor.execute(statement)

            # If the count is 1, then table exists
            count = cursor.fetchone()[0]
            logger.debug(f"{statement} RETURNED {str(count)}.")

        except sqlite3.IntegrityError:
            logger.error("Integrity Error: This violates the database's integrity rules.")
        except sqlite3.ProgrammingError as pe:
            logger.error(f"Programming Error: {pe}")
        except sqlite3.OperationalError as oe:
            logger.error(f"Operational Error: {oe}")
        except sqlite3.DatabaseError as de:
            logger.error(f"Database Error: {de}")
        except sqlite3.DataError as dte:
            logger.error(f"Data Error: {dte}")
        except sqlite3.InterfaceError as ie:
            logger.error(f"Interface Error: {ie}")
        except sqlite3.InternalError as ine:
            logger.error(f"Internal Error: {ine}")
        except sqlite3.NotSupportedError as nse:
            logger.error(f"Not Supported Error: {nse}")
        except (Exception, BaseException) as error:
            logger.error(f"Unrecognized error checking for records in {table} ({type(error).__name__}): {str(error)}")
        return count

    # -------------------------------------------------------------------------
    # From: https://en.ittrip.xyz/python/sqlite-error-handling
    async def db_execute(self, SQL_statements):
        """Executes a list of SQL statements in a transaction."""
        status = False
        cursor = self.conn.cursor()

        try:
            # Start a transaction
            self.conn.execute('BEGIN TRANSACTION;')

            if isinstance(SQL_statements, str):
                logger.debug(f"db_execute: {SQL_statements}")
                cursor.execute(SQL_statements)
            

            if isinstance(SQL_statements, list):
                for statement in SQL_statements:
                    logger.debug(f"db_execute: {statement}")
                    cursor.execute(statement)
            
            # Commit the transaction
            self.conn.commit()
            status = True
        except sqlite3.Error as e:
            # Roll back any changes if an error occurs
            logger.debug(f"Error {e}")
            try:
                self.conn.rollback()
                logger.error("Transaction failed. Rollback was successful.")
            except Exception: 
                logger.error("Transaction failed. Rollback was NOT successful. Please contact support.")
        # TODO Add fallback error handling

        return status
    async def query(self, SQL_statement):
        """
        Executes a query and returns the results.
        SQL_statement: The SQL statement to
            execute.
        Returns: A list of dictionaries containing the results.
        """
        results = []
        try:
            cursor = self.conn.cursor()
            cursor.execute(SQL_statement)
            columns = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
        except sqlite3.Error as e:
            logger.error(f"Error executing query: {e}")
        return results

    # -------------------------------------------------------------------------
    async def create_table(self, table_definition):
        """
        Creates a table in the database.
        
        table_name: String 
        table_definition: JSON Object
            {
                "table_name": "[table_name]", 
                "table_fields": [
                    {"name": "[field_name]", "type": "[field_type]", "attributes": "[field_attributes]"},
                    {"name": "[field_name]", "type": "[field_type]" }
                ],
                "table_indexes": [
                    {"name": "[index_name]", "fields": ["field_name"], "attributes": "[index_attributes]"},
                    {"name": "[index_name]", "fields": ["field_name"]}
                ]
            }
        
        Returns True if successful. False otherwise.
        """
        status = False
        table_name = table_definition.get("table_name", "")
        if table_name != "" and "table_fields" in table_definition:
            logger.debug(f"Creating table: {table_name}" )
            SQLstr = ""

            SQLstr += f"CREATE TABLE IF NOT EXISTS {table_name}"
            SQLstr += " ("
            first_field = True
            for field in table_definition["table_fields"]:
                if not first_field:
                    SQLstr += ", "
                else:
                    first_field = False
                SQLstr += field["name"] + " " + field["type"]
                if "attributes" in field :
                    SQLstr += f" {field["attributes"]}"
            SQLstr += ");"
            status = await self.db_execute([SQLstr])
        else:
            logger.error("Table name not found in table definition.")

        return status
    # -------------------------------------------------------------------------

    async def insert(self, table_name, table_fields, table_blob_fields={}):
        """
        Inserts a record into a table.
        table_name: String 
        table_fields: Array of JSON Objects
                    {
                    "field_name" : "field_value" | field_value,
                    "field_name" : "field_value" | field_value
                    }
        Field values must be SQL "string ready". 
        Strings must have single quotes around them,
           and must be appropriately escaped for the ' character.
        """
        status = False
        logger.debug(f"Inserting into: {table_name}")


        field_list = []
        values_list = []
        for field in table_fields:
            match table_fields[field]:
                case str():
                    field_list.append(field)
                    values_list.append(f"'{table_fields[field]}'")
                case int(), float():
                    field_list.append(field)
                    values_list.append(table_fields[field])
                case bool():
                    field_list.append(field)
                    values_list.append(misc.iif(table_fields[field], 1, 0))
                case _:
                    logger.debug(f"Unhandled variable type: {field} ({str(type(table_fields[field]))})")

        SQLstr = f"INSERT INTO {table_name} ({", ".join(field_list)}) VALUES ({", ".join(values_list)});"

        status = await self.db_execute([SQLstr])

        return status
    
    # -------------------------------------------------------------------------
    def drop_table(self, table_name):
        """
        Drops a table from the database.
        table_name: String 
        Returns True if successful. False otherwise.
        """
        status = False
        logger.debug(f"Dropping table: {table_name}" )
        SQLstr = f"DROP TABLE IF EXISTS {table_name};"
        status = self.db_execute([SQLstr])
        return status

    # -------------------------------------------------------------------------
    async def cache_file(self, content, uuid = None, attributes={}):
        """
        Stores file content in the filecache table.
        content: The file contents to be cached
        uuid: If a UUID is passed, and it exists in the filecache, 
              this will replace the content. 
              Otherwise, a new entry will be created.
        attributes: A dictionary of values to be added or updated with the row 
              where the file is sstored. 
        Returns:
        - If successful, returns the UUID value of the saved file.
        - Returns None otherwise
        """
        status = False
        logger.debug("Caching file" )
        if attributes:
            attributes["compressed"] = CONTENT_COMPRESSION

            if self.type == "sqlite3":
                logger.debug("Storing file in SQLite3 database")
                status = await type_sqlite3.store_blob_to_db(self.conn, uuid, content, attributes )
            
        return status
    # -------------------------------------------------------------------------
    async def retrieve_file(self, uuid):
        """
        Retrieves a file from the filecache table.
        uuid: The UUID of the file to be retrieved.
        Returns: The file content if successful. None otherwise.
        """
        content_dict = {}
        logger.debug(f"Retrieving file using uuid='{uuid}'" )

        if self.type == "sqlite3":
            content_dict = type_sqlite3.retrieve_blob_from_db(self.conn, uuid)


        return content_dict
    # -------------------------------------------------------------------------

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def oscal_datatype(datatype):
    """
    Aligns the datatype to the OSCAL datatype.
    datatype: The datatype to be aligned
    Returns: The aligned datatype
    """

# -----------------------------------------------------------------------------
def db_datatype(datatype, database_type):
    """
    Aligns the datatype to the database type.
    datatype: The datatype to be aligned
    database_type: The database type
    Returns: The aligned datatype
    """
    aligned_datatype = datatype


    if database_type == "sqlite3":
        match datatype:
            case "string", "":
                aligned_datatype = "TEXT"
            case "date-time":
                aligned_datatype = "NUMERIC"
            case "integer", "boolean":
                aligned_datatype = "INTEGER"
            case "REAL":
                aligned_datatype = "REAL"
            case "BLOB":
                aligned_datatype = "BLOB"
            case _:
                logger.warning(f"{datatype} is an unrecognized datatype for {database_type}.")
                aligned_datatype = "TEXT"
    else:
        logger.error(f"Unsupported database type: {database_type}")
        aligned_datatype = "TEXT"

    return aligned_datatype

# =============================================================================
#  --- MAIN: Only runs if the module is executed stand-alone. ---
# =============================================================================
if __name__ == '__main__':
    print("Database Class. Not intended to be run as a stand-alone file.")
