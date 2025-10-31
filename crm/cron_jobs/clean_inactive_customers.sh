#!/bin/bash
# navigate to the project directory
cd /home/ms/alx-backend-graphql_crm/

deleted_count=$(python3 manage.py shell -c "

from datetime import timedelta, date
from crm.models import Customer

one_year_ago = data.today() - timedelta(days=365)
deleted, _ Customer.objects.filter(last_order_date__lt=one_year_ago).delete()

print(deleted)

")

# Log delete
echo "$(date '+%Y-%m-%d %H:%M:%S') - Deleted $deleted_count inactive customers" >> /tmp/customer_cleanup_log.txt