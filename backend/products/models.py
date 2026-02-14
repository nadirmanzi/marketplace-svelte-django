from django.db import models
from users.models import User

class Product(models.Model):
    PRODUCT_AVAILABILITY_CHOICES = [
        ("available", "Available"),
        ("out_of_stock", "Out of Stock"),
        ("coming_soon", "Coming soon"),
    ]

    PRODUCT_PUBLICATION_CHOICES = [
        ("published", "Published"),
        ("draft", "Draft"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    availability = models.CharField(
        choices=PRODUCT_AVAILABILITY_CHOICES, default="available", max_length=20
    )
    publication = models.CharField(
        choices=PRODUCT_PUBLICATION_CHOICES, default="unpublished", max_length=255
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
