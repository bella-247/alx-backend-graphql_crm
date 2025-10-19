# from crm.models import Customer, Product

# Customer.objects.create(name="John Doe", email="john@example.com", phone="+251912345678")
# Product.objects.create(name="Laptop", price=1200.00, stock=5)
# Product.objects.create(name="Mouse", price=25.00, stock=50)

# seed_db.py
from crm.models import Customer
print(list(Customer.objects.all()))
# customers = [
#     {"name": "Bella", "email": "bella@example.com"},
#     {"name": "Mia", "email": "mia@example.com"},
#     # {"name": "John", "email": "john@example.com"},
# ]

# for c in customers:
#     Customer.objects.get_or_create(**c)

# print(f"{len(customers)} customers added successfully!")
