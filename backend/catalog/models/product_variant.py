import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from catalog.managers import ProductVariantManager


class ProductVariant(models.Model):
    """
    Sellable product variant.
    """

    variant_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="variants",
        db_index=True,
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        blank=True,
        help_text="Stock Keeping Unit — unique identifier for inventory. Auto-generated if not provided.",
    )
    name = models.CharField(
        max_length=255,
        help_text="Variant label, e.g. 'Size L - Red'.",
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Variant-specific price. If null, falls back to product base_price.",
    )

    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Current available stock. Updated via locked transactions.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible key-value attributes (color, size, weight, etc.).",
    )

    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords(excluded_fields=["stock_quantity"])
    objects = ProductVariantManager()

    class Meta:
        app_label = "catalog"
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        ordering = ["name"]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def clean(self):
        if self.price is not None and self.price < 0:
            raise ValidationError({"price": "Variant price cannot be negative."})

        self.check_discount_integrity()

    def check_discount_integrity(self):
        eff_price = self.effective_price
        if eff_price is None:
            return

        from .discount import Discount

        discount_filter = models.Q()
        has_scope = False

        # Safe on unsaved inline variants: use ids, not model instances.
        if self.pk:
            discount_filter |= models.Q(variants__pk=self.pk)
            has_scope = True
        if self.product_id:
            discount_filter |= models.Q(products__pk=self.product_id)
            has_scope = True

        if not has_scope:
            return

        max_discount = (
            Discount.objects.filter(discount_filter, is_active_override=False)
            .filter(discount_type=Discount.DiscountType.FIXED_AMOUNT)
            .aggregate(models.Max("value"))["value__max"]
        )

        if max_discount and eff_price < max_discount:
            raise ValidationError(
                {
                    "price": (
                        f"Effective price (${eff_price}) cannot be lower than the fixed "
                        f"discount (${max_discount}) applied to this variant or its parent product."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def effective_price(self) -> Decimal:
        return self.price if self.price is not None else self.product.base_price
