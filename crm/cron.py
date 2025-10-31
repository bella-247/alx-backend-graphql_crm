import logging
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql/", retries=1, verify=False
)

client = Client(transport=transport, fetch_schema_from_transport=False)


def log_crm_heartbeat():
    log_file = "/tmp/crm_heartbeat_log.txt"
    logging.basicConfig(
        filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s"
    )
    query = gql(
        """ 
        {
            hello
        }
    """
    )

    client.execute(query)
    logging.info("CRM is alive")


def update_low_stock():
    log_file = "/tmp/low_stock_updates_log.txt"
    logging.basicConfig(
        filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s"
    )
    mutation = gql(
        """
        mutation {
            update_low_stock_products {
                products {
                    id
                    name
                    stock
                }
                message
            }
        }
    """
    )

    try:
        response = client.execute(mutation)
        data = response.get("updateLowStockProducts", {})

        updated_products = data.get("products", [])
        message = data.get("message", "")

        if updated_products:
            for product in updated_products:
                logging.info(
                    f"Updated product: {product.name} with stock {product.stock}"
                )

        else:
            logging.info("No low stock products found.")

        logging.info(f"Message: {message}")

    except Exception as e:
        logging.error(f"Error updating low stocks {str(e)}")
