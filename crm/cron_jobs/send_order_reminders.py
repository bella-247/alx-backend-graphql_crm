#!/usr/bin/env python3
import datetime
import logging
from gql import gql, Client
from gql.transport.requests import RequestHTTPTransport

log_file = "/tmp/order_reminders_log.txt"
logging.basicConfig(
    filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s"
)


transport = RequestHTTPTransport(
    url="http://localhost:8000/graphql", verify=False, retries=1
)

client = Client(transport=transport, fetch_schema_from_transport=False)

query = gql(
    """ 
    {
        orders(orderDate_Gte: "%s") {
            id
            customer {
                email 
            }
        }
    }
    """
    % (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
)

try:
    result = client.execute(query)
    orders = result.get("orders", [])

    if not orders:
        logging.info("No pending orders found within the last 7 days.")

    else:
        for order in orders:
            order_id = order["id"]
            email = order["customer"]["email"]
            logging.info(f"Reminder: Order {order_id} for customer {email}")

except Exception as e:
    logging.error(f"Error fetching orders: {e}")
    print(f"Failed {str(e)}")
