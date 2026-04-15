"""
Business logic for discount lifecycle operations.
"""

from django.db import DatabaseError, transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from catalog.models import Category, Discount, Product, ProductVariant
from users.exceptions import NotFoundError, ServiceValidationError


class DiscountService:
    """
    Encapsulates create/update/delete logic for discounts.
    """

    @classmethod
    @transaction.atomic
    def create_discount(cls, *, performed_by, **data) -> Discount:
        categories = data.pop("categories", [])
        products = data.pop("products", [])
        variants = data.pop("variants", [])

        try:
            discount = Discount(**data)
            discount.save()
            cls._set_scopes(
                discount=discount,
                categories=categories,
                products=products,
                variants=variants,
            )
            discount.full_clean()
            discount.save()
            return discount
        except DjangoValidationError as e:
            raise ServiceValidationError(
                "; ".join(msg for messages in e.message_dict.values() for msg in messages)
            )
        except DatabaseError:
            raise

    @classmethod
    @transaction.atomic
    def update_discount(cls, *, performed_by, discount: Discount, **data) -> Discount:
        categories = data.pop("categories", None)
        products = data.pop("products", None)
        variants = data.pop("variants", None)

        for field, value in data.items():
            if hasattr(discount, field):
                setattr(discount, field, value)

        try:
            discount.save()
            cls._set_scopes(
                discount=discount,
                categories=categories,
                products=products,
                variants=variants,
                partial=True,
            )
            discount.full_clean()
            discount.save()
            return discount
        except DjangoValidationError as e:
            raise ServiceValidationError(
                "; ".join(msg for messages in e.message_dict.values() for msg in messages)
            )
        except DatabaseError:
            raise

    @classmethod
    @transaction.atomic
    def delete_discount(cls, *, performed_by, discount: Discount) -> None:
        discount.delete()

    @staticmethod
    def _set_scopes(
        *,
        discount: Discount,
        categories=None,
        products=None,
        variants=None,
        partial: bool = False,
    ) -> None:
        if categories is not None or not partial:
            categories_qs = Category.objects.filter(pk__in=(categories or []))
            if len(categories or []) != categories_qs.count():
                raise NotFoundError("One or more categories do not exist.")
            discount.categories.set(categories_qs)

        if products is not None or not partial:
            products_qs = Product.objects.filter(pk__in=(products or []))
            if len(products or []) != products_qs.count():
                raise NotFoundError("One or more products do not exist.")
            discount.products.set(products_qs)

        if variants is not None or not partial:
            variants_qs = ProductVariant.objects.filter(pk__in=(variants or []))
            if len(variants or []) != variants_qs.count():
                raise NotFoundError("One or more variants do not exist.")
            discount.variants.set(variants_qs)
