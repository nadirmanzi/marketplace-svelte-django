import uuid

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from catalog.managers import DiscountManager


class Discount(models.Model):
    """
    Discount rules applicable to categories, products, or variants.
    """

    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        FIXED_AMOUNT = "fixed_amount", "Fixed Amount"

    discount_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Internal name for the discount, e.g., 'Summer Sale'")
    description = models.TextField(blank=True, default="", help_text="Optional description for customers.")

    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The value of the discount (e.g., 10 for 10% or $10).",
    )

    start_date = models.DateTimeField(db_index=True)
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Optional end date. If blank, discount runs indefinitely.",
    )
    is_active_override = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Manual kill-switch. If true, the discount is stopped regardless of dates.",
    )

    categories = models.ManyToManyField("catalog.Category", related_name="discounts", blank=True)
    products = models.ManyToManyField("catalog.Product", related_name="discounts", blank=True)
    variants = models.ManyToManyField("catalog.ProductVariant", related_name="discounts", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()
    objects = DiscountManager()

    class Meta:
        app_label = "catalog"
        verbose_name = "Discount"
        verbose_name_plural = "Discounts"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.get_discount_type_display()} - {self.value})"

    def clean(self):
        if self.value <= 0:
            raise ValidationError({"value": "Discount value must be greater than zero."})

        if self.discount_type == self.DiscountType.PERCENTAGE and self.value > 100:
            raise ValidationError({"value": "Percentage discounts cannot exceed 100%."})

        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError({"end_date": "End date must be after the start date."})

        if self.discount_type == self.DiscountType.FIXED_AMOUNT and self.pk:
            if self.categories.exists():
                raise ValidationError(
                    {
                        "discount_type": (
                            "Fixed amount discounts cannot be applied to categories. "
                            "Category-wide discounts must use the percentage type."
                        )
                    }
                )

        if self.discount_type == self.DiscountType.FIXED_AMOUNT and self.pk:
            product_ids = self.products.values_list("pk", flat=True)
            min_product_price = self.products.aggregate(models.Min("base_price"))["base_price__min"]

            ProductVariant = apps.get_model("catalog", "ProductVariant")
            min_child_variant_price = (
                ProductVariant.objects.filter(product_id__in=product_ids)
                .annotate(
                    eff_price=models.Case(
                        models.When(price__isnull=False, then="price"),
                        default="product__base_price",
                        output_field=models.DecimalField(),
                    )
                )
                .aggregate(models.Min("eff_price"))["eff_price__min"]
            )

            min_product_scope_price = min_product_price
            if min_product_scope_price is None:
                min_product_scope_price = min_child_variant_price
            elif min_child_variant_price is not None:
                min_product_scope_price = min(min_product_scope_price, min_child_variant_price)

            if min_product_scope_price and self.value > min_product_scope_price:
                raise ValidationError(
                    {
                        "value": (
                            f"Fixed discount ({self.value}) cannot exceed the base price "
                            f"of an associated product/variant ({min_product_scope_price})."
                        )
                    }
                )

            min_variant_price = (
                self.variants.annotate(
                    eff_price=models.Case(
                        models.When(price__isnull=False, then="price"),
                        default="product__base_price",
                        output_field=models.DecimalField(),
                    )
                ).aggregate(models.Min("eff_price"))["eff_price__min"]
            )
            if min_variant_price and self.value > min_variant_price:
                raise ValidationError(
                    {
                        "value": (
                            f"Fixed discount ({self.value}) cannot exceed the price "
                            f"of an associated variant ({min_variant_price})."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        if self.is_active_override:
            return False

        now = timezone.now()
        if self.start_date > now:
            return False

        if self.end_date and self.end_date < now:
            return False

        return True
