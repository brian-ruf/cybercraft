import os
from loguru import logger
import json
import uuid
import pickle
from typing import Any, Optional
from common import misc
from common import database
from common import network
import asyncio
import qasync


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Release and Support File Patterns
# DEFAULT_EXCLUDE_TAG_PATTERNS = ["-rc", "-milestone"] # Ignore release tags with these substrings.
DEFAULT_EXCLUDE_VERSIONS = ["v1.0.0-rc1", "v1.0.0-rc2", "v1.0.0-milestone1", "v1.0.0-milestone2", "v1.0.0-milestone3"] 
SUPPORT_FILE_PATTERNS    = {
    "_metaschema_RESOLVED.xml":   "metaschema",    # OSCAL specification files
    "_schema.xsd":                "xml-schema",       # OSCAL XML schema validation files
    "_schema.json":               "json-schema",      # OSCAL JSON schema validation files
    "_xml-to-json-converter.xsl": "xml-to-json", # OSCAL XML to JSON converters
    "_json-to-xml-converter.xsl": "json-to-xml" # OSCAL JSON to XML converters
    } 

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# GitHub root URLs
GitHub_API_root = "https://api.github.com"
GitHub_raw_root = "https://raw.githubusercontent.com"
GitHub_release_root = "https://github.com"
http_header = {"Content-type": "application/json"}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# NIST OSCAL GitHub and Dcoumentation URLs
OSCAL_repo = "usnistgov/OSCAL" # Official NIST OSCAL GitHub Repository owner and repository name
OSCAL_repo_API = f'{GitHub_API_root}/{OSCAL_repo}/releases'
OSCAL_Release_URL = f"{GitHub_release_root}/{OSCAL_repo}/releases/tag" # /{tag_name}
OSCAL_asset_downloads = f"{GitHub_release_root}/{OSCAL_repo}/tree" # /{tag_name}
OSCAL_documentation = "https://pages.nist.gov/OSCAL-Reference/models" # /{tag_name}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Data structures for the OSCAL support database
OSCAL_SUPPORT_TABLES={}
OSCAL_SUPPORT_TABLES["oscal_versions"] = {
    "table_name": "oscal_versions",
    "table_fields": [ 
        {"name": "version"               , "type": "TEXT"   , "attributes": "PRIMARY KEY", "label" : "Release Tag", "description": "The GitHub release tag assocaited with the OSCAL version."},
        {"name": "title"                 , "type": "TEXT"   , "label" : "Release Title", "description": "The title of the released version."},
        {"name": "released"              , "type": "NUMERIC", "label" : "Released", "description": "The date and time the version was released."},
        {"name": "github_location"       , "type": "TEXT"   , "label" : "GitHub Location", "description": "The location of the GitHub release for this version of OSCAL."},
        {"name": "documentation_location", "type": "TEXT"   , "label" : "Documentation Location", "description": "The location of documentation for this version."},
        {"name": "acquired"              , "type": "NUMERIC", "label" : "Acquired", "description": "The date and time the support files were loaded into this system."},
        {"name": "successful"            , "type": "NUMERIC", "label" : "Successful", "description": "Indicates whether all support files were acquired successfully."}
    ]
}
OSCAL_SUPPORT_TABLES["oscal_support"] = {
    "table_name": "oscal_support",
    "table_fields": [
        {"name": "version"         , "type": "TEXT", "attributes": "KEY", "label" : "OSCAL Version","description": "The OSCAL version."},
        {"name": "model"           , "type": "TEXT", "label" : "OSCAL Model", "description": "The OSCAL model name, exactly as it appears in OSCAL syntax."},
        {"name": "type"            , "type": "TEXT", "label" : "Support File Type", "description": "The type of support file."},
        {"name": "filecache_uuid"  , "type": "TEXT", "label" : "Cache UUID", "description": "The filecache UUID of the support file for this OSCAL version and model."}
    ]
}
OSCAL_SUPPORT_TABLES["filecache"] = database.OSCAL_COMMON_TABLES["filecache"]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OSCAL_DATA_TYPES = {}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class OSCAL_support:
    def __init__(self, db_conn, db_type="sqlite3"):
        self.ready      = False     # Is the support capability available?
        self.db_conn    = db_conn   # The support database connection string or path and filename 
        self.db_type    = db_type   # The support database type (sqlite3, mysql, postgresql, mssql, etc.)
        self.db_state   = "unknown" # The state of the support database (unknown, not-present, empty, populated)
        # self.db_obj     = None      # The support database object 
        self.versions   = {}        # Supported OSCAL versions available within the support database, and support references
        self.extensions = {}        # Supported OSCAL extensions available within the support database, and support references
        self.backend    = None      # If working within an application, this is the backend object

        self.db = database.Database(self.db_type, self.db_conn)
        if self.db is not None:
            asyncio.create_task(self.async_init())
        else:
            logger.error("Unable to create support database object.")
            self.ready = False
    # -------------------------------------------------------------------------
    async def async_init(self):
        self.ready = await self.startup()
    # -------------------------------------------------------------------------
    @classmethod
    async def create(cls, db_conn, db_type="sqlite3"):
        """Async factory method to create and initialize OSCAL_support"""
        self = cls(db_conn, db_type)
        if self.db is not None:
            self.ready = await self.startup()
        return self
    # -------------------------------------------------------------------------
    async def startup(self, check_for_updates=False, refresh_all=False):
        """
        Perform startup tasks required to provide OSCAL support.

        1 Check for tables
          - If tables do not exist:
            - create tables
            - set state to "empty"
          - If tables exist, check for data
            - If no data, set state to "empty"
            - If data exists, set state to "populated"
        2 If state is "empty", check for connection to GitHub
         - If cannot connect to GitHub, EXIT (cannot proceed)
         - If connected to GitHub, update database
           - If update fails, EXIT (cannot proceed)
           - If update succeeds, set state to "populated"
        3 If state is "populated" set self.ready to True
        """
        status = False
        if self.db_state == "unknown": 
            # status = await self.__check_for_tables()
            status = await self.db.check_for_tables(OSCAL_SUPPORT_TABLES)

            if status: # Tables exist
                # TODO: Check database structure against current
                #       structure and modify fields as needed.
                status = await self.__load_versions()
                if status:
                    self.db_state = "populated"
                    self.ready = True
                else:
                    self.db_state = "empty"
            else:
                logger.error("Unable to initiate OSCAL support capability. Exiting.")
                self.ready = False

        if self.db_state == "empty":
            status = await self.__get_oscal_versions()

            if status:
                self.db_state = "populated"
                self.ready = True
            else:
                logger.error("Unable to update OSCAL support capability. Exiting.")
                self.ready = False
       
        return status
    # -------------------------------------------------------------------------
    # async def __check_for_tables(self):
    #     """
    #     Check for the presence of the OSCAL support tables in the database.
    #     """
    #     status = True
    #     for key in OSCAL_SUPPORT_TABLES:
    #         if self.db.table_exists(key):
    #             status = status and True
    #         else:
    #             self.__status_messages(f"Creating Table: {key}")
    #             table_exists = await self.db.create_table(OSCAL_SUPPORT_TABLES[key])
    #             status = status and table_exists

    #     return status
    # -------------------------------------------------------------------------
    async def __load_versions(self):     
        """
        Load supported OSCAL versions and support references into memory.
        """
        status = False

        logger.debug("Loading OSCAL versions into memory.")
        query = "SELECT * FROM oscal_versions ORDER BY released DESC"
        results = await self.db.query(query)
        if results is not None:
            for entry in results:
                self.versions[entry["version"]] = {
                    "title"                 : entry.get("title", ""),
                    "released"              : entry.get("released", ""),
                    "github_location"       : entry.get("github_location", ""),
                    "documentation_location": entry.get("documentation_location", ""),
                    "acquired"              : entry.get("acquired", ""),
                    "successful"            : entry.get("successful", None),
                }
            status = True

        return status

    # -------------------------------------------------------------------------
    async def __get_oscal_versions(self, fetch="latest"):
        """Pulls OSCAL version information and support files from GitHub and loads it into the database."""
        status = True
        OSCAL_versions = []
        fetch_all = (fetch == "all")
        fetch_latest = (fetch == "latest")
        fetch_one = (fetch.startswith("v"))
        
        self.__status_messages("Fetching OSCAL release informaiton from GitHub...")
        
        # Add small delay to allow UI updates
        await asyncio.sleep(0)
        
        repo_releases = await network.async_api_get(GitHub_API_root + "/repos/" + OSCAL_repo + "/releases")
        self.__status_messages("Fetching OSCAL release information from GitHub...done.")

        if repo_releases is not None:
            total_releases = len(repo_releases)
            
            self.__status_messages(f"Found {total_releases} releases in the OSCAL GitHub repository.")
            for idx, entry in enumerate(repo_releases, 1):
                self.__status_messages(f"Inspecting release {idx} of {total_releases}...")
                # Yield control periodically
                if idx % 2 == 0:  # More frequent yields
                    await asyncio.sleep(0)
                
                if not entry.get("draft", False):
                    oscal_version = entry.get("tag_name", "").lower()
                    self.__status_messages(f"Found non-draft OSCAL Version {oscal_version}...")
                    if (oscal_version not in DEFAULT_EXCLUDE_VERSIONS):
                        self.__status_messages(f"Found non-excluded OSCAL Version {oscal_version}") 
                        
                        ok_to_continue = (fetch_all or 
                                        (fetch_latest and oscal_version not in self.versions) or
                                        (fetch_one and oscal_version == fetch))

                        if ok_to_continue:
                            self.__status_messages(f"Processing {oscal_version} release...")
                            release_date = entry.get("published_at", "0000-00-00T00:00:00Z")
                            release_name = entry.get("name", "")
                            github_location = f"{OSCAL_Release_URL}/{oscal_version}" 
                            documentation_location = f"{OSCAL_documentation}/{oscal_version}" 
                            await self.__clear_oscal_version(oscal_version)
                            
                            # Split up the database operations to allow more UI updates
                            await asyncio.sleep(0)
                            
                            logger.info(f"Learning {oscal_version}, released {release_date} ...")
                            if await self.db.insert("oscal_versions", {
                                "version": oscal_version,
                                "released": release_date,
                                "title": release_name,
                                "github_location": github_location,
                                "documentation_location": documentation_location,
                                "acquired": misc.oscal_date_time_with_timezone()
                            }):
                                OSCAL_versions.append(oscal_version)
                                if "assets" in entry:
                                    # Process assets in chunks
                                    await self.__get_support_files(oscal_version, entry["assets"])
                            else:
                                logger.error(f"Unable to insert OSCAL version {oscal_version} into support database.")
                        else:
                            self.__status_messages(f"Skipping {oscal_version} release.")
                    else:
                        self.__status_messages(f"Skipping excluded OSCAL Version {oscal_version}...")
                
                # Add small delay after processing each version
                await asyncio.sleep(0)
        else:
            logger.error("Unable to fetch release information from GitHub.") 
            status = False

        if status:
            self.__status_messages("OSCAL version information loaded successfully.")
            self.__status_messages(f"Learned {len(OSCAL_versions)} OSCAL versions.")
            self.__status_messages(f"OSCAL versions: {', '.join(OSCAL_versions)}")

        return status

    # -------------------------------------------------------------------------
    async def __get_support_files(self, version, assets):
        """Modified to use async network operations and process in chunks"""
        status = False
        chunk_size = 3  # Process assets in chunks of 3
        
        # Split assets into chunks
        for i in range(0, len(assets), chunk_size):
            chunk = assets[i:i + chunk_size]
            tasks = []
            
            for asset in chunk:
                asset_name = asset.get("name", "")
                for pattern in SUPPORT_FILE_PATTERNS:
                    if pattern in asset_name:
                        tasks.append(self.__process_single_asset(version, asset, pattern))
            
            # Process chunk of assets concurrently
            if tasks:
                await asyncio.gather(*tasks)
                # Allow UI update after each chunk
                await asyncio.sleep(0)
        
        status = True
        return status

    # -------------------------------------------------------------------------
    async def __process_single_asset(self, version, asset, pattern):
        """Helper method to process a single asset"""
        asset_name = asset.get("name", "")
        asset_URL = asset.get("browser_download_url", "")
        model_name = asset_name.replace("oscal_", "").replace(pattern, "")

        # Special case for SSP and POAM
        if model_name == "ssp": model_name = "system-security-plan"
        if model_name == "poam": model_name = "plan-of-action-and-milestones"
        
        uuid_value = str(uuid.uuid4())
        # acquired = misc.oscal_date_time_with_timezone()
        
        self.__status_messages(f"Downloading {asset_name}...")
        
        # Perform database inserts
        
        await self.db.insert("oscal_support", {
            "version": version,
            "model": model_name,
            "type": SUPPORT_FILE_PATTERNS[pattern],
            "filecache_uuid": uuid_value
        })
        

        # Download file content asynchronously
        content = await network.async_download_file(asset_URL, asset_name)

        # await self.db.insert("filecache", {
        #     "uuid": uuid_value,
        #     "filename": asset_name,
        #     "original_location": asset_URL,
        #     "acquired": acquired
        # })


        if content:
            attributes = {
                "filename": asset_name,
                "original_location": asset_URL,
                "mime_type": "application/octet-stream",
                "file_type": SUPPORT_FILE_PATTERNS[pattern],
                "acquired": misc.oscal_date_time_with_timezone()
            }
            await self.db.cache_file(content, uuid_value, attributes)
            self.__status_messages(f"Downloaded [{version}] {asset_name}")
        else:
            self.__status_messages(f"Failed to download {asset_name}", "error")
    # -------------------------------------------------------------------------
    async def __clear_oscal_version(self, version):
        """
        Clear all support content for the specified OSCAL version.
        """
        status = False

        sql_commands = [
            # "BEGIN TRANSACTION;",
            f""" 
            WITH uuids_to_delete AS (
                SELECT filecache_uuid
                FROM oscal_support
                WHERE version = '{version}'
            )
            DELETE FROM filecache
            WHERE uuid IN (SELECT filecache_uuid FROM uuids_to_delete);""",
            f"DELETE FROM oscal_support WHERE version = '{version}';",
            f"DELETE FROM oscal_versions WHERE version = '{version}';"
            # "COMMIT;"
        ]

        status = await self.db.db_execute(sql_commands)

        if status: 
            logger.info(f"Successfully deleted support information for version {version}")
        else:
            logger.error(f"Unable to deleted support information for version {version}")

        return status
    
    async def __clear_oscal_versions(self):
        """
        Clear all support content for all OSCAL versions.
        """
        status = False
        if self.versions:
            for version in self.versions:
                status = await self.__clear_oscal_version(version)
                self.__status_messages(f"Clearing support content for version {version}")
                if not status:
                    break
        else:
            status = True
        return status
    # -------------------------------------------------------------------------
    def __status_messages(self, status="", level="info"):
        """Enhanced status message handling"""
        if self.backend is not None:
            self.backend.status_update(status, level)
        logger.info(status)
    # -------------------------------------------------------------------------
    async def update(self, fetch="latest", backend=None):
        """Modified update method to be more granular"""
        status = False
        self.backend = backend
        
        try:
            match fetch:
                case "all":
                    self.__status_messages("Starting full refresh of OSCAL support content...")
                    status = await self.__clear_oscal_versions()
                case "latest":
                    self.__status_messages("Checking for new OSCAL versions...")
                    status = True
                case _:
                    if fetch.startswith("v"):
                        self.__status_messages(f"Updating specific version: {fetch}")
                        status = await self.__clear_oscal_version(fetch)
                    else:
                        logger.error(f"Invalid update directive: {fetch}")
                        status = False
            
            if status:
                # Get OSCAL versions with periodic status updates
                status = await self.__get_oscal_versions(fetch)
            
            # Final reload of versions
            await self.__load_versions()
            
            self.__status_messages("Update process completed.")
            
        except Exception as e:
            logger.error(f"Error during update: {e}")
            self.__status_messages(f"Error during update: {str(e)}", "error")
            status = False
            
        return status


    # -------------------------------------------------------------------------
    def supported(self, oscal_version, assets):
        """
        Identifies the approppriate support files and downloads them.
        Adds them to the support database.
        """
        status = False


        return status

# -----------------------------------------------------------------------------

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Main
if __name__ == '__main__':
    print("The OSCAL Support Class is not intended to be run as a stand-alone file.")
