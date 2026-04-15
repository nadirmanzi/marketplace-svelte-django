"""
Admin forms for catalog models.

CategoryAdminForm adds circular-reference validation that works
in the Django admin interface, preventing administrators from
accidentally creating broken category hierarchies.
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import Category, Discount


class DiscountAdminForm(forms.ModelForm):
    """
    ModelForm for Discount validating M2M fields seamlessly in the Django admin.
    """

    class Meta:
        model = Discount
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        discount_type = cleaned_data.get("discount_type")
        categories = cleaned_data.get("categories")

        if discount_type == Discount.DiscountType.FIXED_AMOUNT and categories:
            self.add_error(
                "discount_type",
                ValidationError(
                    "Fixed amount discounts cannot be applied to categories. "
                    "Category-wide discounts must use the percentage type."
                ),
            )
        return cleaned_data


class CategoryAdminForm(forms.ModelForm):
    """
    ModelForm for Category with circular-reference detection.

    Used by the admin site to prevent assigning a category
    as its own ancestor (which would break tree traversal).
    """

    class Meta:
        model = Category
        fields = "__all__"

    def clean_parent(self):
        """Validate that setting this parent won't create a cycle."""
        parent = self.cleaned_data.get("parent")
        if parent is None:
            return parent

        instance = self.instance

        # Cannot be own parent
        if instance.pk and parent.pk == instance.pk:
            raise ValidationError("A category cannot be its own parent.")

        # Walk up the chain to detect cycles
        if instance.pk:
            visited = {instance.pk}
            ancestor = parent
            while ancestor is not None:
                if ancestor.pk in visited:
                    raise ValidationError(
                        "This would create a circular reference in the category tree."
                    )
                visited.add(ancestor.pk)
                ancestor = ancestor.parent

        return parent
