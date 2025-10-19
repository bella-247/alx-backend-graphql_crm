import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
import re


# Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")


# Queries
class CRMQuery(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")


# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        if Customer.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")

        if phone and not re.match(r"^\+?\d{7,15}$|^\d{3}-\d{3}-\d{4}$", phone):
            raise ValidationError("Invalid phone format")

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(
            customer=customer, message="customer created successfully"
        )


class CustomerInput(graphene.InputObjectType):
    name = (graphene.String(required=True),)
    email = (graphene.String(required=True),)
    phone = (graphene.String(required=False),)


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(graphene.NonNull(CustomerInput), required=True)

    customers = graphene.List(lambda: CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        created_customers = []
        errors = []

        for data in input:
            if Customer.objects.filter(email=data.email).exists():
                errors.append(f"Email {data.email} already exists")
                continue

            if data.phone and not re.match(
                r"^\+?\d{7,15}$|^\d{3}-\d{3}-\d{4}$", data.phone
            ):
                errors.append(f"Invalid phone format for {data.email}")
                continue

            customer = Customer(
                name=data.name,
                email=data.email,
                phone=data.phone or "",
            )
            customer.save()
            created_customers.append(customer)

        return BulkCreateCustomers(customers=created_customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    product = graphene.Field(ProductType)
    message = graphene.String()

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            raise ValidationError("Price must be positive")
        if stock < 0:
            raise ValidationError("Stock cannot be negative")

        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product, message="Product created successfully")


class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)
    message = graphene.String()

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            raise ValidationError("Invalid customer ID")

        if not product_ids:
            raise ValidationError("At least one product is required")

        products = []
        total = 0

        for pid in product_ids:
            try:
                product = Product.objects.get(id=pid)
                products.append(product)
                total += float(product.price)
            except Product.DoesNotExist:
                raise ValidationError(f"Invalid product ID: {pid}")

        if not order_date:
            order_date = timezone.now()

        order = Order.objects.create(
            customer=customer, total_amount=total, order_date=order_date
        )
        order.products.set(products)
        return CreateOrder(order=order, message="Order created successfully")


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
