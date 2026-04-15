"""
Final pricing service for sellable product variants.

Source of truth:
- base_price: variant base_price (or inherited product base_price)
- final_price: discounted price when a matching active discount exists
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import QuerySet

from catalog.models import Category, Discount, Product, ProductVariant


TWO_DP = Decimal("0.01")


@dataclass(frozen=True)
class PricingResult:
    base_price: Decimal
    final_price: Decimal
    discount_amount: Decimal
    has_discount: bool
    applied_discount_id: str | None
    applied_discount_name: str | None
    applied_discount_type: str | None
    applied_discount_value: Decimal | None
    applied_scope: str | None


class FinalPricingService:
    """
    Resolves final pricing for models.
    """

    @classmethod
    def get_variant_pricing(cls, *, variant: ProductVariant) -> PricingResult:
        """
        Return original and final prices for a sellable variant.
        """
        base_price = variant.base_price if variant.base_price is not None else (variant.product.base_price if variant.product_id else Decimal("0.00"))
        discount = cls._resolve_discount_for_variant(variant)
        return cls._build_result(base_price=base_price, discount=discount)

    @classmethod
    def for_variant(cls, *, variant: ProductVariant) -> PricingResult:
        # Backward-compat alias.
        return cls.get_variant_pricing(variant=variant)

    @classmethod
    def get_product_pricing(cls, *, product: Product) -> PricingResult:
        """
        Return original and final prices for a product.
        """
        base_price = product.base_price or Decimal("0.00")
        discount = cls._resolve_discount_for_product(product)
        return cls._build_result(base_price=base_price, discount=discount)

    @classmethod
    def get_category_discount(cls, *, category: Category) -> PricingResult:
        """
        Return discount information for a Category.
        """
        discount = cls._resolve_discount_for_category(category)
        return cls._build_result(base_price=Decimal("0.00"), discount=discount)

    @staticmethod
    def _active_discounts() -> QuerySet:
        # Manager exposes active() on queryset, not directly on manager.
        return Discount.objects.get_queryset().active()

    @classmethod
    def _resolve_discount_for_variant(cls, variant: ProductVariant) -> tuple[Discount, str] | None:
        """
        Resolve one discount with strict precedence:
        category > product > variant.
        """
        product = variant.product
        current_price = variant.base_price if variant.base_price is not None else (product.base_price if product else Decimal("0.00"))

        category_ids = cls._category_ancestor_ids(product.category) if product else []
        if category_ids:
            category_discount = cls._pick_best_discount(
                cls._active_discounts().filter(categories__in=category_ids).distinct(),
                current_price,
            )
            if category_discount:
                return category_discount, "category"

        if product:
            product_discount = cls._pick_best_discount(
                cls._active_discounts().filter(products=product).distinct(),
                current_price,
            )
            if product_discount:
                return product_discount, "product"

        variant_discount = cls._pick_best_discount(
            cls._active_discounts().filter(variants=variant).distinct(),
            current_price,
        )
        if variant_discount:
            return variant_discount, "variant"

        return None

    @classmethod
    def _resolve_discount_for_product(cls, product: Product) -> tuple[Discount, str] | None:
        """
        Resolve one discount for Product with strict precedence:
        category > product.
        """
        current_price = product.base_price or Decimal("0.00")

        category_ids = cls._category_ancestor_ids(product.category)
        if category_ids:
            category_discount = cls._pick_best_discount(
                cls._active_discounts().filter(categories__in=category_ids).distinct(),
                current_price,
            )
            if category_discount:
                return category_discount, "category"

        product_discount = cls._pick_best_discount(
            cls._active_discounts().filter(products=product).distinct(),
            current_price,
        )
        if product_discount:
            return product_discount, "product"

        return None

    @classmethod
    def _resolve_discount_for_category(cls, category: Category) -> tuple[Discount, str] | None:
        """
        Resolve one discount for Category. Since categories only support percentage,
        we use a dummy price of 100 to compare percentages easily.
        """
        category_ids = cls._category_ancestor_ids(category)
        if category_ids:
            category_discount = cls._pick_best_discount(
                cls._active_discounts().filter(categories__in=category_ids).distinct(),
                Decimal("100.00"),
            )
            if category_discount:
                return category_discount, "category"
        return None


    @staticmethod
    def _category_ancestor_ids(category: Category | None) -> list[str]:
        """
        Return category id chain from current category to root.
        """
        if category is None:
            return []

        ids: list[str] = []
        cursor = category
        while cursor is not None:
            ids.append(str(cursor.pk))
            cursor = cursor.parent
        return ids

    @staticmethod
    def _pick_best_discount(discounts: QuerySet, price: Decimal) -> Discount | None:
        """
        Choose discount with largest monetary reduction inside one scope.
        """
        best_discount = None
        best_amount = Decimal("0.00")

        for discount in discounts:
            amount = FinalPricingService._compute_discount_amount(
                base_price=price,
                discount_type=discount.discount_type,
                discount_value=discount.value,
            )
            if amount > best_amount:
                best_amount = amount
                best_discount = discount

        return best_discount

    @staticmethod
    def _compute_discount_amount(*, base_price: Decimal, discount_type: str, discount_value: Decimal) -> Decimal:
        if base_price <= 0:
            return Decimal("0.00")

        if discount_type == Discount.DiscountType.PERCENTAGE:
            raw = (base_price * discount_value) / Decimal("100")
            return raw.quantize(TWO_DP, rounding=ROUND_HALF_UP)

        # fixed_amount
        return min(discount_value, base_price).quantize(TWO_DP, rounding=ROUND_HALF_UP)

    @classmethod
    def _build_result(cls, *, base_price: Decimal, discount: tuple[Discount, str] | None) -> PricingResult:
        normalized_base = base_price.quantize(TWO_DP, rounding=ROUND_HALF_UP)
        if discount is None:
            return PricingResult(
                base_price=normalized_base,
                final_price=normalized_base,
                discount_amount=Decimal("0.00"),
                has_discount=False,
                applied_discount_id=None,
                applied_discount_name=None,
                applied_discount_type=None,
                applied_discount_value=None,
                applied_scope=None,
            )

        selected_discount, scope = discount
        amount = cls._compute_discount_amount(
            base_price=normalized_base,
            discount_type=selected_discount.discount_type,
            discount_value=selected_discount.value,
        )
        final_price = max(Decimal("0.00"), normalized_base - amount).quantize(
            TWO_DP,
            rounding=ROUND_HALF_UP,
        )

        return PricingResult(
            base_price=normalized_base,
            final_price=final_price,
            discount_amount=amount,
            has_discount=True,
            applied_discount_id=str(selected_discount.discount_id),
            applied_discount_name=selected_discount.name,
            applied_discount_type=selected_discount.discount_type,
            applied_discount_value=selected_discount.value,
            applied_scope=scope,
        )


# Backward compatibility for existing imports.
PricingService = FinalPricingService
