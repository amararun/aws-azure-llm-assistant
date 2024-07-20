from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import FileResponse
import mysql.connector
import os
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

# Database connection details for AWS
aws_database_name = "example_schema"
aws_host = "db-instance-example123.us-east-1.rds.amazonaws.com"
aws_user = "admin_example"
aws_password = "awsExamplePassword!456"

# Database connection details for Azure
azure_database_name = "example_db"
azure_host = "example-server3.mysql.database.azure.com"
azure_user = "example_admin"
azure_password = "azureExamplePassword!789"

def create_aws_connection():
    connection = mysql.connector.connect(
        host=aws_host,
        user=aws_user,
        password=aws_password,
        database=aws_database_name
    )
    return connection

def create_azure_connection():
    connection = mysql.connector.connect(
        host=azure_host,
        user=azure_user,
        password=azure_password,
        database=azure_database_name,
        ssl_disabled=True
    )
    return connection

def get_connection(cloud: str):
    if cloud == "azure":
        return create_azure_connection()
    elif cloud == "aws":
        return create_aws_connection()
    else:
        raise ValueError("Invalid cloud provider specified")

@app.get("/sqlquery/")
async def sqlquery(sqlquery: str, cloud: str, request: Request):
    logger.debug(f"Received API call: {request.url} with cloud parameter: {cloud}")
    try:
        connection = get_connection(cloud)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        cursor = connection.cursor()
        cursor.execute(sqlquery)
        
        # Handle queries that return results
        if cursor.description is not None:
            headers = [i[0] for i in cursor.description]
            results = cursor.fetchall()
            cursor.close()

            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".txt") as temp_file:
                temp_file.write(" | ".join(headers) + "\n")
                for row in results:
                    temp_file.write(" | ".join(str(item) for item in row) + "\n")
                temp_file_path = temp_file.name

            logger.debug(f"Query executed successfully, results written to {temp_file_path}")
            # Return the file response
            response = FileResponse(path=temp_file_path, filename="output.txt", media_type='text/plain')
            return response
        
        # Handle non-SELECT queries
        else:
            connection.commit()
            cursor.close()
            logger.debug("Non-SELECT query executed successfully")
            return {"status": "Query executed successfully"}

    finally:
        connection.close()
        logger.debug("Database connection closed")

@app.middleware("http")
async def remove_temp_file(request, call_next):
    logger.debug(f"Processing request: {request.url}")
    response = await call_next(request)
    if isinstance(response, FileResponse) and os.path.exists(response.path):
        try:
            os.remove(response.path)
            logger.debug(f"Temporary file {response.path} removed successfully")
        except Exception as e:
            logger.error(f"Error removing temp file: {e}")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout=120)
