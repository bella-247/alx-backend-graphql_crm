import re
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter


# Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        fields = ("id", "customer", "products", "total_amount", "order_date")


# Queries
class Query(graphene.ObjectType):
    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)

class CRMQuery(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilter,
        order_by=graphene.List(of_type=graphene.String),
    )

    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter,
        order_by=graphene.List(of_type=graphene.String),
    )
    
    all_orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilter,
        order_by=graphene.List(of_type=graphene.String),
    )
    hello = graphene.String(default_value="Hello, GraphQL!")

    def resolve_all_customers(self, info, **kwargs):
        queryset = Customer.objects.all()
        order_by = kwargs.get("order_by")
        if order_by:
            queryset = queryset.order_by(*order_by)
        return queryset

    def resolve_all_products(self, info, **kwargs):
        queryset = Product.objects.all()
        order_by = kwargs.get("order_by")
        if order_by:
            queryset = queryset.order_by(*order_by)
        return queryset

    def resolve_all_orders(self, info, **kwargs):
        queryset = Order.objects.all()
        order_by = kwargs.get("order_by")
        if order_by:
            queryset = queryset.order_by(*order_by)
        return queryset


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
