# aws-azure-llm-assistant
LLM Analytics Assistant. Prototype. Connected to AWS and Azure MySQL DataWarehouse

---

Build an Analytics Assistant App: Flowise AI, Text-to-SQL, FastAPI. Connect to any Data Warehouse. AWS-Azure MySQL

In my earlier videos and posts I showed how the Analytics Assistant App works, connecting to and analyzing data on AWS RDS MySQL and Azure MySQL, with table sizes ranging from 1 Million to 10 Million records….smoothly converting natural language text to SQL….summarizing, merging and creating customer profiles. 
This is similar to a setup I have used for a live client use case. This is a barebones version for sharing publicly.
Links Below:
MEDIUM: LLM Analytics Assistant: Simplifying Data Transformation & Insights. AWS & Azure MySQL.
LINKEDIN : GenAI App | LLM Analytics Assistant: Simplifying Data Transformation & Insights. AWS & Azure MySQL DW Example
What we will cover in this article:
Example of Text-to-SQL
Implementation: Step 1 - FastAPI Server - Code
Implementation: Step 2 - FastAPI Server - Deploy
Implementation: Step 3 - Flowise AI : Setup Custom Tool
Implementation: Step 4 : Flowise AI : Setup Chatflow 
Implementation: Step 5 : Flowise AI : Deploy on your Website
Data Warehouse - Azure - AWS - Others
Additional Consideration: Security, Monitoring, Tracing, Feeback
Cost Considerations
Full Data Ingestion & Split Processing: Scenarios and Costs
Agentic Framework, Accuracy & Complex Workflows
Working with LLM / GPTs for coding: My Top 5 Favorite Techniques
Resources 

LLM Analytics Assistant App : What it Does.
In my previous article and videos, I demoed a prototype Analytics Assistant App analyzing data on AWS RDS MySQL and Azure MySQL, with table sizes ranging from 1 Million to 10 Million records.
I used a FastAPI server in the middle to allow ease of connectivity to any backend database as well as front end of our choice.
I've deployed this setup on my public website using Flowise AI, and I also have a custom GPT version. In both cases my FastAPI Server and backend databases are same. 
In the demo, I took a bank credit card analytics use case as an example. The customer table had a million records, and the transaction table had ten million records. We had to summarize the transaction table, extract derived variables, merge it back with the customer table and finally create customer sales activity profiles.
Examples: Text-to-SQL and Analysis
In the query below I am asking the assistant to summarize the 10 Million transactions table with a bunch of variables….in natural language and with spellos and sometimes a bit fuzzy instructions. See the query generated at backend and passsed to database. It is absolutely perfect. And the LLM Model here was gpt-3.5-turbo

Text to SQL Example: Summarizing transaction table with 10 Million Records with addtion of derived variables 
I then merged the transaction summary with the 1 Million customer table. Now I am asking the assistant to create a customer sales activity profile with additional derived variables. This one is grouped by housing variable.

Text To SQL Example: Creating a Customer Sales Activity Profile Report with additional derived variables
Finally, I ask the assistant to create a consolidated customer sales activity profile combining the individual ones generated earlier (grouped by housing/ response tag/ education variables)

---

Analytics Assistant LLM App: How it works
Shared in detail in my initial video. Summary below.
Natural Language Query: User inputs a natural language query… this could be done through Flowise AI, Custom GPT, or other LLM platforms… or any other front end of your choice
Text-to- SQL :The LLM App (like Flowwise AI or Custom GPT) takes this natural language input and converts it to SQL… this is where the magic happens… natural language to SQL conversion. 
Send Query as API Call: The SQL query is then sent as an API call to the FastAPI server… this uses Custom Tool/ Function Calling capabilites of an LLM Model
Database Connection: FastAPI server connects to the AWS or Azure Data Warehouse… this server is the middleman, ensuring data is retrieved securely and efficiently…and sent back to whoever is making the API call.
Query Results: The database processes the SQL query and sends back the results to the FastAPI server… 
API Response: FastAPI server receives these results and sends them back to the LLM App… 
Display Results: The LLM App takes this data and servers it to the user… 

---

How to Guide | Step 1 -  FastAPI Server : Coding 
All coding done by LLMs, in this case by ChatGPT-4/4o. And by the way some of my earlier FastAPI Servers were coded by the free ChatGPT 3.5. And it was also incredibly good. I found that the easiest is to share one of my existing FastAPI Server codes and instruct the LLM to share a revised code incorporating with my new instructions on database server connections, how i want the endpoints to be setup, how I want the output to be shared and so on.
A FastAPI server allow us to create an API endpoint with python code. [See resources section for links to articles and videos explaining basics of FastAPI servers]
Complete Code available on my GitHub repo. You can pick up from there also and make any necessary changes.
In sections below I am sharing explanations of various sections of the code. In case of questions and for modifications, easiest is to ask your favorite LLM to guide you. That's how I had started off….and continue to do so wherever I get a code that i need to unpack and understand.
In the first section of code below, I am importing libraries, setting up FastAPI instance and database connection details. 
For my live app on client site, the database details are stored as an environment variable. Have put it here on main code for prototype purposes only. 
A function is defined that chooses the right database connection (AWS or Azure) to be used based on the parameters passed by the LLM Custom Tool / Function. I have also enabled slightly more detailed logging in order to trace the complete flow on my server logs. Very useful to figure out where an issue might be happening. 
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

In the code below, I define an endpoint /sqlquery/, that takes two string parameters: a full SQL Query this is passed by the LLM Assistant / Tool and also the cloud provider (AWS / Azure). 
The code executes the SQL query, and if it's a SELECT query, it fetches the results, writes them to a temporary text file, and returns the file to the user. 
For non-SELECT queries, it commits the changes to the database and returns a success message.
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

In this last section of the code, I have added a middleware that processes HTTP requests… it makes sure that any temporary file created is removed after the response is sent. 
The if __name__ == "__main__" block runs the FastAPI app with Uvicorn, listening on all network interfaces at port 8000, with a timeout of 120 seconds.
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
The only other piece needed is the requirements.txt file. 
fastapi==0.70.0
uvicorn==0.15.0
mysql-connector-python
python-multipart
How To Guide | Step 2 - FastAPI Server: Deploy
You can deploy on any web service platform of your choice.
I find Render to be the easiest to deploy. Just takes a few minutes. I also use Heroku for some of my apps. Both are reasonably prices. Render has a great free tier. If you need always on then a Starter pack would work costing USD 7 p.m. and you are charged for the time that you keep the server live…. and if you suspend the web service then you are not charged for that part.
See Videos and Guides in resources section on how to deploy FastAPI server / web service on Render. Quick steps below
In the 'New' Button on top choose 'Web Service'. 
Just link and point to your Github Repo and that's it.
Language : Python 3
Start Command : uvicorn app:app - host 0.0.0.0 - port $PORT`

Choose Starter plan if you wish, and hit 'Deploy Web Service' and you are all set. It takes a minute or two to deploy
Once deployed you will get the URL which would something like this:
https://your-github-repo-name.onrender.com/
This is the URL of your FastAPI Server and it is always listening for any incoming requests.
This is now to be used in the next step to link up Flowise AI to your FastAPI Server
You can now test it using a service like Postman (see links in resources section on how to use Postman) . Another way is to simply copy the full API Call URL and paste into your web browser… an example with SHOW TABLES for AWS is shown below:
https://your-github-repo-name.onrender.com/sqlquery/?sqlquery=SHOW%20TABLES&cloud=aws
If all is well then, your browser window will display the results of the query (file download box in my case as i am outputting a file) 
In case of errors, you would then need to share the error back with LLM / GPTs to debug. Postman is super helpful in these situations.

---

How To Guide | Step 3 - Flowise AI: Setup Custom Tool
Leon Van Zyl has the absolutely marvelous step-by-step guides for Flowise AI. The complete Flowise playlist is a must watch for anybody wanting to develop an app on Flowise. 
Flowise AI Tutorial #11- Custom Tools, OpenAI Functions and Webhooks (youtube.com)
I would recommend using that as a guide to setup your Custom Tool as well as to setup ChatFlows. Below I am sharing the key details required for the custom tool setup as well as some tips.
Screenshot of my Custom Tool on Flowise AI

Tool Description that I am using shared below.
Replace with your actual endpoint URL per section above and your actual schema names
The description helps the Tool Agent on when and how to use the tool.

Execute API call to a based on user question . User question would be converted into a SQL Query and passed as a parameter. Another parameter is the cloud database provide ie azure or aws. See sample API endpoint URL call below.

Database server in both cases is MySQL. So make sure that queries are MySQL compliant

If user refers to 'schema' or 'database' it refers to the following
in Azure : give-your-schema-name-here
in AWS : give-your-schema-name-here

All the rest of the schema/databases on the MySQL server are system ones and not relevant

Here's a API end point example for quick reference. Just sample. use all correct values as per javascript function
https://give-your-api-endpoint-url-here.com/sqlquery?sqlquery=SHOW%20TABLES%20FROM%20schema_defaults&cloud=aws

Please wait for upto 180  seconds for query response to come in as the server can be slow sometimes
Input Schema that I am using 
This instructs the tool agent that the SQL query string has to stored into variable called 'sqlquery' and the data warehouse (aws or azure) specified by the user can take values either 'aws' or 'azure' and needs to be stored into variable called cloudVar. This is used while making the http fetch request to FastAPI endpoint.
JavaScript Function that i am using shared below. 
Replace with your actual FastAPI endpoint URL after deploying on web server per earlier section. For any modifications and changes I tend to just share an existing JavaScript function like the one below and instruct LLM / GPT to make necessary changes.
The JavaScipt executes a http fetch request using 'GET' method to the API endpoint URL that we created. As you can see in the code, full URL is constructed using the 'sqlquery' and 'cloudVar' variables stored earlier in input schema, in the exact format that the FastAPI server is expecting. 
/*
NOTE FOR TOOL AGENT : Please wait for upto 180  seconds for query response to come in as the server can be slow sometimes
*/

const fetch = require('node-fetch');

// Properly encode the query parameters
const sqlQuery = encodeURIComponent($sqlquery);
const cloudVar = encodeURIComponent($cloudVar);

const url = `https://your-api-endponit-url-here.com/sqlquery/?sqlquery=${sqlQuery}&cloud=${cloudVar}`;

const options = {
    method: 'GET',
    headers: {
        'Content-Type': 'application/json'
    }
};

try {
    const response = await fetch(url, options);
    const text = await response.text();
    return text;
} catch (error) {
    console.error(error);
    return '';
}

---

How To Guide | Step 5 -  Flowise AI: Setup Chatflow 
Sharing below the image of my ChatFlow. It's a pretty straightforward setup to replicate. I was using gpt-turbo-3.5 that time as gpt-4o-mini yet to be released. Have changed it now. I also a version with Claude and Google Gemini. But at that time OpenAI one seems to work the smoothest.

---

How To Guide | Step 6 - Flowise AI: Deploy on your Website
I simply use the embed URL to embed it into my website. There are multiple options available
Click on Embed Code Icon <> on top of ChatFlow
Go to Share Chatbot -> Enable Public Sharing -> Customize Options
Use the embed URL link to embed on public website / intranet site.

Refer to Leo's Video for a step-by-step guide and various options for customization.
Adding AI Chatbots to Websites - FlowiseAI Tutorial #10 (youtube.com)
This is how it looks on my website

---

Data Warehouse - Azure - AWS - Others
Using FastAPI as a middle processing layer (described in next section) you can connect to any Data Warehouse / Databases. You just need the right connection parameters. You would typically be provided this by your database admin. But in case you wish to setup one from scratch, sharing some quick tips below.
My existing client use case requires me to work with data warehouse schemas on AWS RDS MySQL and also Azure MySQL. For the purposes of the prototype, I have setup both instances.
For those interested in setting up AWS / Azure MySQL instances, sharing some quick tips below:
Numerous videos and guides availale. See resources section below for a few. Also request LLM / GPT to guide you step by step. Wherever you get stuck you can share a screen shot of the AWS / Azure screen and let the LLM / GPT guide you.
For the very first connection test, best to do in Google Colab / Jupyter to make sure connection works. You can use something like below:

import mysql.connector

# Replace placeholders with your credentials
database_name = "example_schema"
host = "db-instance-example123.us-east-1.rds.amazonaws.com"  
user = "admin_example"
password = "awsExamplePassword!456"
def create_connection():
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database_name
    )
    return connection

connection = create_connection()
connection
For UI and admin access to the data warehouses I prefer to use phpMyAdmin. Best to install it via Dockerfile route rather than installing all the dependencies one-by-one. Also check video links in resources section. Just ask LLM / GPT to guide you step-by-step on how to do it. Make sure to setup up user and password there.
Later on, once your FastAPI server is working, make sure to modify security setting in both AWS and Azure to allow inbound access only from the IP Addresses of your FastAPI server. In my case FastAPI Server was deployed on Render and Render provides these IP Addresses. As will all other web services providers.

Additional Consideration: Security , Monitoring, Tracing, Feeback
Briefly touching upon some considerations. Plan to cover those in more detail in future posts.
Tracing Message Flow : Flowise AI allows multiple options to trace complete message flow. Especially useful in debugging complex flows. I use Langsmith. Very easy to setup and use. See Leon's tutorial (link in resources section)
Message Feedback: Very easy to enable message feedback in Flowise. Users can give a thumbs up or a thumbs down with a message box for further inputs. See Leon's tutorial (link in resources section)
Monitoring Chats: Chat histories can be monitored directly by going into Settings in Chat Flow window -> View Messages. Chat history is by default in a SQL Lite database in default database path specified during Flowise AI Setup. Flowise AI also supports storing of messages in MySQL or PostgresSQL. Excellent video from business_24.ai on how to export chat histories and related aspects (link in resources section)
Database Credentials: I store them in Environment Variable. Just for the prototype purposes have put that directly in the code for ease of explanation. Recommended to keep them as environment variable.
API Keys: You can also setup your own API keys to control access to the FastAPI endpoint. I have another version for this. Will share in future posts. But fairly simple to do. The most simplest implementation requires setting up a key as an environment variable and getting LLM / GPT to modify the FastAPI Server code and Custom tool JavaScript code accordingly and pass and additional variable in the input schema of Custom Tool. Can also be used for user access control by having the LLM Assistant request for an API key before proceeding, which is then passed as a query parameter down the line.
Inbound IP Address: I have setup inboud IP Address whitelist on both Azure and AWS to only allow incoming requests from the Render Server. This is to guard against any unauthorized API calls from unknown IP
Selective Access: for instance, to certain tables / schemas as well as read write access. Can be enabled via phpMyadmin and integrated downstream.
Prompt Injections: Whole big area. Lot of options available. Was not a high priority for my client use case so have not gone much into this.
Standard IT Security: These include Enterprise Login, SSO, other user authentications, server side measures to manage against DDoS attacks, unauthorized server access, control over public IP address, setting up of VPN if required etc which the IT world has been doing for ages. 
Cost Considerations for LLM Analytics App
Shared in my initial video. Sharing below a quick overview of expenses associated with the LLM app platform, LLM model usage and FastAPI server. There can be a wide variance here based on the particular use case. 
LLM App Platform Costs
Flowise AI:
The LLM app builder I'm using is Flowise AI, which is open-source and free. However, you still need to host it somewhere.
For this prototype, I've hosted it on Render, which costs me around $7 per month. And only charged pro-rata for the time the server is turned on. You can host it pretty much on any platform of your choice including AWS / Azure / GCP / Railway / Heroku / Digital Ocean etc.

Scalability:
This setup is less intensive, suitable for small-scale use cases.
If you need to handle hundreds or tens of thousands of messages per minute, the $7 server won't suffice, and you'll need a more robust solution. Either on Render or elsewhere

LLM Model Costs
GPT-3.5:
For this prototype, on a particular day I ran approximately 470 API requests over 10 hours, costing around a total of just $1. This involved working with a 1 million customer dataset and a 10 million transaction dataset, creating synthetic data, merging, summarizing, and generating cross tabs.
The total token usage was about 1.9 million, with 1.8 million input tokens and around 52,000 output tokens.
This cost was for a non-optimized setup. Proper optimization can significantly reduce the costs.

GPT-4o-mini:
This was before GPT-4o-mini was launched. If I were to use gpt-4o-mini now the cost would be around half of that.

Optimization:
High input token count is due to sending the entire history with every query. This can be optimized to reduce costs.
Output tokens averaged around 110 per query, representing a reasonable size for SQL queries or cross tab results.

FastAPI Server Costs
Hosting:
The FastAPI server, which acts as an API endpoint, is also hosted on Render for $7 per month. Again charged pro-rata for the time the server is turned on.
This server only charges when it is up and running, making it a cost-effective solution for small-scale use cases.

Server Load:
For this prototype, the FastAPI server is primarily acting as a messenger, handling queries and responses without any heavy processing.
If the server were to handle processing tasks like data cleaning, transformation, statistical procedures, or model building, a higher capacity server would be required.

Full Data Ingestion: Scenario and Costs
This is a very different scenario that what we have discussed above. For example, building a machine learning model with OpenAI's code interpreter requires ingesting the entire dataset, leading to exponentially high API costs. 
Full data ingestion by the LLM model is not always necessary and can significantly increase costs, potentially by 1000X or more
For many use cases, processing can be done separately, and the LLM only needs to pass SQL queries or Python commands, avoiding the need for full data ingestion. This is the use case presented in this article, where processing is happening at the database server end. In another of my use cases part of processing is happening at database server end and part of it on the FastAPI server.

Split Workflow Approach:
For scenarios requiring full data ingestion, split the workflow into multiple modules. The LLM should ingest only the necessary and smallest amount of data directly, while the remaining data processing and model building should happen separately on the database server and/ or Python server.
Planning to share a prototype with this approach in near future.

---

Agentic Framework, Accuracy & Complex Workflows
This was a simple prototype. And even with gpt-3.5 i got a fairly good accuracy on SQL Queries. Less than 10% of the more complex SQL Queries were wrong. It was easy for me to catch, but that might not work for many scenarios. I am sure that using gpt-4o or claude-3.5-sonnet would significantly improve query accuracy
For further improvements, an agentic framework is strongly recommended with 'Supervisor' or a 'Query Checker' agent checking the query prepared by the initial 'Query Preparer' Agent. Flowise AI supports this. Check out Leon's excellent guide on the same:
How to Build AI Agent Teams (NO-CODE!) | Flowise Agentflows Tutorial (youtube.com)
And Flowise AI recently launched Sequential Agents, a way more powerful framework to incorporate complex flows including : calling agents conditionally, run agents in parallel, human-in-the-loop , state management and much more. See Leon's brilliant video guide below:
Master Sequential Agents: Build Complex AI Apps with Flowise (youtube.com)

---

Working with LLM / GPTs for coding: My Top 5 Favorite Techniques
Voice Typing : Some of my instructions for code generation or modification go into pages. I tend to use the Voice Typing mode in Google Docs. Simply 'talk' 'whatever i need and dump the whole thing onto LLM / GPT.
Video Screen Grab: Example : In one of the video the contributor had shared instructions and codes on screen. I took a screen grab and asked LLM / GPT to guide me through that step-by-step.
Vision based Guidance: Example : I am filling some form in Azure / AWS and get confused about options or maybe don't know where to find something particular … i just share a screen shot with GPT and ask it to guide me .. it will then tell me something like "On bottom window there is an icon that looks like so-and-so … click there … then do so-and-so" .. or "For your prototype needs you need not choose so-and-so option but so-and-so option will work"
"I want to do the same thing": Example: Sometimes I will take a article like this one and dump it on a LLM / GPT and tell them that I want to do the same thing .. and can it explain in simple words what is happening … and then further ask it to guide me step by step.
Video Transcript: Example : For a particularly long and complex video tutorial, I pulled out the transcript and shared with LLM / GPT … to explain in simple words .. and then guide me step by step. See my article 𝗛𝗼𝘄 𝘁𝗼 𝘀𝘂𝗺𝗺𝗮𝗿𝗶𝘇𝗲 & 𝗮𝗻𝗮𝗹𝘆𝘇𝗲 𝗬𝗼𝘂𝗧𝘂𝗯𝗲 𝘃𝗶𝗱𝗲𝗼𝘀 𝘄𝗶𝘁𝗵 𝗔𝗜 : 𝗧𝘄𝗼 𝗙𝗥𝗘𝗘 𝗮𝗻𝗱 𝗘𝗔𝗦𝗬 𝗼𝗽𝘁𝗶𝗼𝗻𝘀 | by Amar Harolikar | Medium. 

Additional Resources
Numerous posts and videos available. Very grateful to all the contributors. Sharing just a few for quick reference. And anywhere you get stuck don't hesitate to ask LLM/ GPT to guide you step by step. In fact I will very often share a screen grab from a video and request LLM to guide me for that step-by-step.
FastAPI
FastAPI Setup a Server in 10 Minutes | Installation, Setup & Route Creation (youtube.com)
FastAPI Tutorial: An Introduction to Using FastAPI | DataCamp
Using FastAPI to Build Python Web APIs - Real Python
How to deploy a FastAPI API or APP on Render for free (youtube.com)

Postman
What is Postman and why everyone use it ? (youtube.com)
Learn Postman in 15 Minutes (youtube.com)

Setting up AWS and Azure MySQL and phpMyadmin
Create AWS RDS and Connect Through PhpMyadmin | Connect RDS Through CLI (youtube.com)
Create Azure Database for MySQL Flexible Server using Azure Portal | How to Create MySQL Flex Server (youtube.com)
phpMyAdmin Tutorial: Introduction to phpMyAdmin | What is phpMyAdmin? (youtube.com)

Monitoring , Tracing, Message Feedback
Analysing Chatflows using LangSmith - FlowiseAI Tutorial #7 (youtube.com)
(476) 8 SECRET Flowise AI Features You DIDN'T Know Existed (Supercharge Your Workflow!) - YouTube (for message feedback and other features)
(476) Flowise Database - Use MySQL and SQLite to export Flowise Messages to Excel for FREE - YouTube
(476) Flowise Database - Use MySQL and SQLite to export Flowise Messages to Excel for FREE - YouTube
