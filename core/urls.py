from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import ViewSets
from users.views import UserViewSet
from customers.views import CustomerViewSet
from accounts.views import SavingsAccountViewSet
from transactions.views import TransactionViewSet
from audit.views import AuditViewSet

# Create router and register ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'accounts', SavingsAccountViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'audit', AuditViewSet)

urlpatterns = [
    # API Root and ViewSets
    path('', include(router.urls)),
] + router.urls
