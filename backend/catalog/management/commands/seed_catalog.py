import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from catalog.models import Category
from catalog.services.product_services import ProductService, VariantService

User = get_user_model()

class Command(BaseCommand):
    help = 'Generates mock categories, products, and variants for testing/development.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting mock data generation...")

        # Ensure we have a user to act as the creator/owner
        admin = User.objects.filter(is_staff=True).first()
        if not admin:
            admin = User.objects.create_superuser(
                email="admin@example.com",
                password="admin",
                full_name="Admin User"
            )
            self.stdout.write(self.style.SUCCESS('Created default admin (admin@example.com) to own products.'))
        else:
            self.stdout.write(f'Using existing staff user: {admin.email}')

        with transaction.atomic():
            self._generate_data(admin)

        self.stdout.write(self.style.SUCCESS("Mock data generation successfully completed!"))

    def _generate_data(self, admin):
        # 1. Create Core Categories
        self.stdout.write("Creating categories...")
        tech = self.create_category("Technology (Mock)", "electronics, computers, and tech gadgets.")
        apparel = self.create_category("Apparel (Mock)", "clothing, shoes, and lifestyle apparel.")
        home = self.create_category("Home & Kitchen (Mock)", "furniture, tools, and kitchen appliances.")

        # Subcategories
        laptops = self.create_category("Laptops (Mock)", "High performance computers", tech)
        wearables = self.create_category("Wearables (Mock)", "Watches and fitness trackers", tech)
        shoes = self.create_category("Footwear (Mock)", "Shoes and sneakers", apparel)

        # 2. Tech Products
        self.stdout.write("Creating mock products and variants...")
        
        # Product 1: High-end Laptop
        try:
            laptop = ProductService.create_product(
                performed_by=admin,
                name="Zenith ProBook 15",
                description="The ultimate productivity machine with a 15-inch 4K OLED display and 24-core processor.",
                base_price=Decimal("1999.00"),
                category=laptops.pk
            )
            VariantService.create_variant(
                performed_by=admin,
                product=laptop,
                name="16GB RAM / 512GB SSD",
                price=Decimal("1999.00"),
                stock_quantity=30,
                metadata={"ram": "16GB", "storage": "512GB SSD", "color": "Space Gray"}
            )
            VariantService.create_variant(
                performed_by=admin,
                product=laptop,
                name="32GB RAM / 1TB SSD",
                price=Decimal("2499.00"),
                stock_quantity=15,
                metadata={"ram": "32GB", "storage": "1TB SSD", "color": "Space Gray"}
            )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Skipped laptop: {e}"))

        # Product 2: Smartwatch
        watch = ProductService.create_product(
            performed_by=admin,
            name="Pulse Watch Series X",
            description="Next generation health tracking, GPS, and multi-day battery life.",
            base_price=Decimal("299.99"),
            category=wearables.pk
        )
        for color in ["Midnight Black", "Starlight Silver", "Rose Gold"]:
            VariantService.create_variant(
                performed_by=admin,
                product=watch,
                name=color,
                price=Decimal("299.99"),
                stock_quantity=random.randint(10, 50),
                metadata={"color": color, "size": "44mm"}
            )

        # 3. Apparel
        # Product 3: Running Shoes
        shoe = ProductService.create_product(
            performed_by=admin,
            name="AeroGlide Ultralight Runners",
            description="Feather-light running shoes with responsive foam technology for everyday marathons.",
            base_price=Decimal("140.00"),
            category=shoes.pk
        )
        
        colors = ["Neon Green", "Carbon Black", "Arctic White"]
        sizes = ["8", "9", "9.5", "10", "11"]
        
        for color in colors:
            for size in sizes:
                # Add a bit of price variation for specific sizes randomly
                price = Decimal("140.00") if size not in ["11"] else Decimal("145.00")
                VariantService.create_variant(
                    performed_by=admin,
                    product=shoe,
                    name=f"{color} - Size {size}",
                    price=price,
                    stock_quantity=random.randint(0, 20),
                    metadata={"color": color, "size": size}
                )

        # Product 4: Home Appliance
        appliance = ProductService.create_product(
            performed_by=admin,
            name="BrewMaster Pro Espresso",
            description="Professional grade espresso machine for your kitchen counter.",
            base_price=Decimal("850.00"),
            category=home.pk
        )
        VariantService.create_variant(
            performed_by=admin,
            product=appliance,
            name="Stainless Steel",
            price=Decimal("850.00"),
            stock_quantity=8,
            metadata={"finish": "Stainless Steel"}
        )
        VariantService.create_variant(
            performed_by=admin,
            product=appliance,
            name="Matte Black Edition",
            price=Decimal("900.00"),
            stock_quantity=3,
            metadata={"finish": "Matte Black"}
        )

        self.stdout.write(f"Generated {Category.objects.count()} categories and successfully seeded all products/variants.")


    def create_category(self, name, description, parent=None):
        cat, created = Category.objects.get_or_create(
            name=name,
            defaults={"description": description, "parent": parent}
        )
        if not created and parent and cat.parent != parent:
            cat.parent = parent
            cat.save()
        return cat
