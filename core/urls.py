from django.urls import path
from rest_framework.routers import DefaultRouter

# Import views here when you create them
# from . import views

router = DefaultRouter()

# Register your viewsets here
# router.register(r'example', views.ExampleViewSet)

urlpatterns = [
    # Add your custom paths here
    # path('custom-endpoint/', views.custom_view, name='custom-endpoint'),
] + router.urls
