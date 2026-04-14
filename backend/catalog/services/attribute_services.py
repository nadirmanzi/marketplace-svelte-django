"""
Business logic for product attributes and category-based inheritance.

Methods:
- get_attributes_for_category: Traverse category tree to collect inherited attributes.
- create_attribute: Define a new attribute.
- assign_to_category: Link attribute to a category.
- validate_attributes: Ensure required attributes are present and typed correctly.
"""

from typing import List, Set, Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from catalog.models import Attribute, Category, CategoryAttribute, AttributeOption
from users.exceptions import ServiceValidationError, NotFoundError


class AttributeService:
    """
    Service for managing the attribute system and hierarchy.
    """

    @staticmethod
    def get_attributes_for_category(category: Category) -> List[Attribute]:
        """
        Fetch all attributes applicable to a category, including inheritance.
        
        Traverses from the given category up to the root, collecting all
        assigned attributes. Specific (child) attributes take precedence in
        ordering, but all are returned.
        """
        attributes = []
        seen_ids = set()
        
        current = category
        while current:
            # Get attributes for this level
            cat_attrs = (
                CategoryAttribute.objects
                .filter(category=current)
                .select_related("attribute")
                .order_by("order")
            )
            
            for ca in cat_attrs:
                if ca.attribute_id not in seen_ids:
                    attributes.append(ca.attribute)
                    seen_ids.add(ca.attribute_id)
            
            current = current.parent
            
        return attributes

    @classmethod
    @transaction.atomic
    def create_attribute(cls, **data) -> Attribute:
        """Create a new attribute definition."""
        options = data.pop("options", [])
        try:
            attribute = Attribute(**data)
            attribute.save()
            
            if attribute.input_type in [Attribute.InputType.SELECT, Attribute.InputType.MULTISELECT]:
                for opt_value in options:
                    AttributeOption.objects.create(attribute=attribute, value=opt_value)
            
            return attribute
        except DjangoValidationError as e:
            raise ServiceValidationError(str(e))

    @staticmethod
    def assign_to_category(category_id: str, attribute_id: str, order: int = 0):
        """Link an attribute to a category."""
        try:
            category = Category.objects.get(pk=category_id)
            attribute = Attribute.objects.get(pk=attribute_id)
            return CategoryAttribute.objects.update_or_create(
                category=category,
                attribute=attribute,
                defaults={"order": order}
            )
        except (Category.DoesNotExist, Attribute.DoesNotExist) as e:
            raise NotFoundError(str(e))


class AttributeValueService:
    """
    Helps assigning and validating values against attribute definitions.
    """

    @staticmethod
    def validate_and_assign(instance, attributes_data: Dict[str, Any], is_variant: bool = False):
        """
        Validate input data against required attributes and save values.
        
        Args:
            instance: Product or ProductVariant instance.
            attributes_data: Dict of {attribute_slug: value}.
            is_variant: True if target is a ProductVariant.
        """
        from catalog.models import ProductAttributeValue, VariantAttributeValue
        
        # 1. Collect all applicable attributes (with inheritance)
        category = instance.category if not is_variant else instance.product.category
        if not category:
            return  # No category, no structured attributes
            
        applicable_attributes = AttributeService.get_attributes_for_category(category)
        
        # 2. Check for missing required attributes
        provided_slugs = attributes_data.keys()
        for attr in applicable_attributes:
            if attr.is_required and attr.slug not in provided_slugs:
                # If it's a variant, maybe it's already defined at product level?
                # For now, we enforce strictness as requested.
                if is_variant:
                    # Check if product already has this attribute
                    if not ProductAttributeValue.objects.filter(product=instance.product, attribute=attr).exists():
                        raise ServiceValidationError(f"Missing required attribute: {attr.name}")
                else:
                    raise ServiceValidationError(f"Missing required attribute: {attr.name}")

        # 3. Assign values
        value_model = VariantAttributeValue if is_variant else ProductAttributeValue
        fk_field = "variant" if is_variant else "product"

        for slug, value in attributes_data.items():
            try:
                attribute = Attribute.objects.prefetch_related("options").get(slug=slug)
            except Attribute.DoesNotExist:
                continue  # Ignore unknown attributes or raise error? Igoring for now.

            # Basic type validation and storage mapping
            defaults = {
                "value_text": None,
                "value_number": None,
                "value_boolean": None,
            }
            
            options_to_set = []

            if attribute.input_type == Attribute.InputType.TEXT:
                defaults["value_text"] = str(value)
            elif attribute.input_type == Attribute.InputType.NUMBER:
                try:
                    defaults["value_number"] = float(value)
                except (ValueError, TypeError):
                    raise ServiceValidationError(f"Attribute {attribute.name} must be a number.")
            elif attribute.input_type == Attribute.InputType.BOOLEAN:
                defaults["value_boolean"] = bool(value)
            elif attribute.input_type in [Attribute.InputType.SELECT, Attribute.InputType.MULTISELECT]:
                # Normalize input to a list of values
                if isinstance(value, list):
                    raw_values = value
                else:
                    raw_values = [value]
                
                # If it's a single SELECT, we only care about the first item
                target_values = [raw_values[0]] if attribute.input_type == Attribute.InputType.SELECT and raw_values else raw_values
                
                for v in target_values:
                    opt = attribute.options.filter(value=v).first()
                    if not opt:
                        raise ServiceValidationError(f"Invalid option '{v}' for attribute {attribute.name}.")
                    options_to_set.append(opt)

            # Update or Create
            val_obj, _ = value_model.objects.update_or_create(
                attribute=attribute,
                **{fk_field: instance},
                defaults=defaults
            )
            
            if options_to_set:
                val_obj.value_options.set(options_to_set)
            else:
                val_obj.value_options.clear()
