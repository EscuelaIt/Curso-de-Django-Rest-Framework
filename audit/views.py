from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Audit
from .serializers import (
    AuditSerializer, AuditListSerializer, AuditDetailSerializer,
    AuditFilterSerializer, AuditSummarySerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="List audit logs",
        description="Retrieve a paginated list of audit log entries.",
        tags=['Audit']
    ),
    retrieve=extend_schema(
        summary="Get audit log details",
        description="Retrieve detailed information about a specific audit log entry.",
        tags=['Audit']
    ),
)
class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing audit logs (read-only)."""
    
    queryset = Audit.objects.all().select_related('user')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['affected_table', 'operation', 'user', 'context']
    search_fields = ['affected_table', 'context']
    ordering_fields = ['operation_date', 'affected_table', 'operation']
    ordering = ['-operation_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AuditListSerializer
        elif self.action == 'retrieve':
            return AuditDetailSerializer
        elif self.action == 'summary':
            return AuditSummarySerializer
        return AuditSerializer
    
    def get_permissions(self):
        """Only admins and operators can view audit logs"""
        if self.request.user.is_authenticated and self.request.user.role in ['ADMIN', 'OPERATOR']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    @extend_schema(
        summary="Get audit summary",
        description="Get audit statistics and summary information.",
        tags=['Audit']
    )
    @action(detail=False, methods=['get'])
    def summary(self, request):
        # Implementation would calculate audit statistics
        summary_data = {
            'total_operations': self.get_queryset().count(),
            'operations_by_type': {},
            'operations_by_table': {},
            'recent_activity': []
        }
        serializer = AuditSummarySerializer(summary_data)
        return Response(serializer.data)