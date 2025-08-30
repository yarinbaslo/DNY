import os
import pymysql
import logging

# Import functions from our other files
import dns_utils
import persona_utils

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    print("start of the run")
    """
    Main handler that orchestrates the DNS cleaning and persona generation.
    """
    db_host = "user-data-db.cx6uo4aykhw3.eu-north-1.rds.amazonaws.com"
    db_user = "admin"
    db_password = "ADMINdny"
    db_name = "user_stats_db"
    openai_api_key ="sk-2x9uA1bCdEfGhIjK76nOpQrStUvWxYz0123TF56789abcd"

    if not all([db_host, db_user, db_password, db_name]):
        logger.error("Missing required environment variables.")
        return {'statusCode': 500, 'body': 'Server configuration error.'}

    connection = None
    try:
        # Establish a single database connection
        connection = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name)
        logger.info("Successfully connected to the database.")

        # --- Call DNS cleaning logic ---
        # The function from dns_utils.py will use the connection
        dns_utils.clean_invalid_dns(connection)

        # --- Call Persona generation logic ---
        # The function from persona_utils.py will use the same connection
        persona_utils.update_user_profile(connection, openai_api_key)

        return {
            'statusCode': 200,
            'body': 'Process completed successfully.'
        }

    except pymysql.MySQLError as e:
        logger.error(f"Database error: {e}")
        return {'statusCode': 500, 'body': f'Database error: {e}'}
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return {'statusCode': 500, 'body': f'An unexpected error occurred: {e}'}
    finally:
        if connection:
            connection.close()
            logger.info("Database connection closed.")
