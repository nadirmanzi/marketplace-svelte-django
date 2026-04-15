import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from catalog.models import Category
from catalog.serializers import CategorySerializer

print("Imports successful!")

# Try serializing if possible
try:
    c = Category(name="Test", slug="test")
    # we don't save to db, just check structure
    s = CategorySerializer(c)
    print("Category Serializer Fields:", s.data.keys())
except Exception as e:
    print(f"Error during serialization: {e}")

