import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from simple_history.models import HistoricalRecords

from catalog.managers import ProductManager


class Product(models.Model):
    """
    Product blueprint template.

    Defines the shared identity and metadata for a group of sellable variants.
    Products are NOT directly listed to end-users.
    """

    class Status(models.TextChoices):
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Default price for variants that don't override it.",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        db_index=True,
        help_text="Seller/creator of this product.",
    )
    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PUBLISHED,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()
    objects = ProductManager()

    class Meta:
        app_label = "catalog"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]
        permissions = [
            ("can_manage_products", "Can create, update, and archive products"),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.base_price is not None and self.base_price < 0:
            raise ValidationError({"base_price": "Base price cannot be negative."})

        self.check_discount_integrity()

    def check_discount_integrity(self):
        if self.base_price is None:
            return

        from .discount import Discount

        max_discount = (
            Discount.objects.get_queryset().active()
            .filter(models.Q(products=self))
            .filter(discount_type=Discount.DiscountType.FIXED_AMOUNT)
            .aggregate(models.Max("value"))["value__max"]
        )

        if max_discount and self.base_price < max_discount:
            raise ValidationError(
                {
                    "base_price": (
                        f"Price ({self.base_price}) cannot be lower than the active fixed "
                        f"discount (${max_discount}) applied directly to this product."
                    )
                }
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            base_slug = self.slug
            counter = 1
            qs = Product.objects.all()
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED

    @property
    def active_variant_count(self) -> int:
        return self.variants.filter(is_active=True).count()
