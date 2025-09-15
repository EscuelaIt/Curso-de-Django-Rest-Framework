from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views import SavingsAccountViewSet
from audit.views import AuditViewSet
from customers.views import CustomerViewSet
from transactions.views import TransactionViewSet

# Import ViewSets
from users.views import UserViewSet

# Create router and register ViewSets
router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"customers", CustomerViewSet)
router.register(r"accounts", SavingsAccountViewSet)
router.register(r"transactions", TransactionViewSet)
router.register(r"audit", AuditViewSet)

urlpatterns = [
    # API Root and ViewSets
    path("", include(router.urls)),
] + router.urls
