import logging
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


log_file = "/tmp/crm_heartbeat_log.txt"
logging.basicConfig(
    filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s"
)

transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql/", retries=1, verify=False
)

client = Client(transport=transport, fetch_schema_from_transport=False)


query = gql(
    """ 
{
    hello
}            
"""
)


def log_crm_heartbeat():
    client.execute(query)
    logging.info("CRM is alive")
