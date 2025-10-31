import logging

log_file = "/tmp/crm_heartbeat_log.txt"
logging.basicConfig(
    filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s"
)

def log_crm_heartbeat():
    logging.info("CRM is alive")
