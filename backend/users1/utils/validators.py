import phonenumbers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def normalize_email(email):
    """
    Normalize the email address by lowercasing the domain part of it.
    """
    if not email:
        return email
    try:
        email_name, domain_part = email.strip().rsplit("@", 1)
    except ValueError:
        # If no @, return the email lowercased (fallback behavior)
        return email.lower()
    else:
        email = email_name + "@" + domain_part.lower()
    return email


def validate_and_normalize_phone(phone_number, country_code=None):
    """
    Validate and normalize phone number to E.164 format.

    Args:
        phone_number (str): The phone number to validate.
        country_code (str): The region code (e.g. 'US') to parsing.

    Returns:
        str: The normalized phone number in E.164 format.

    Raises:
        ValidationError: If the phone number is invalid.
    """
    if not phone_number:
        return None

    try:
        # Parse phone number
        pn = phonenumbers.parse(phone_number, country_code)

        # Check if valid
        if not phonenumbers.is_valid_number(pn):
            raise ValidationError(_("Enter a valid phone number."))

        # Format to E.164
        return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)

    except phonenumbers.NumberParseException:
        raise ValidationError(_("Enter a valid phone number with country code."))
