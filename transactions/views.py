from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Transaction
from accounts.models import SavingsAccount
from .serializers import (
    TransactionSerializer, TransactionCreateSerializer, TransactionListSerializer,
    TransactionStatusSerializer, DepositSerializer, WithdrawalSerializer, TransferSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="List all transactions",
        description="Retrieve a paginated list of all transactions.",
        tags=['Transactions']
    ),
    create=extend_schema(
        summary="Create a new transaction",
        description="Create a new transaction in the banking system.",
        tags=['Transactions']
    ),
    retrieve=extend_schema(
        summary="Get transaction details",
        description="Retrieve detailed information about a specific transaction.",
        tags=['Transactions']
    ),
    update=extend_schema(
        summary="Update transaction",
        description="Update transaction information (limited fields).",
        tags=['Transactions']
    ),
)
class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing banking transactions."""
    
    queryset = Transaction.objects.all().select_related('source_account', 'destination_account', 'user')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['transaction_type', 'status', 'currency', 'source_account', 'user']
    search_fields = ['reference_number', 'description']
    ordering_fields = ['transaction_date', 'amount', 'reference_number']
    ordering = ['-transaction_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TransactionCreateSerializer
        elif self.action == 'list':
            return TransactionListSerializer
        elif self.action == 'change_status':
            return TransactionStatusSerializer
        elif self.action == 'deposit':
            return DepositSerializer
        elif self.action == 'withdrawal':
            return WithdrawalSerializer
        elif self.action == 'transfer':
            return TransferSerializer
        return TransactionSerializer
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @extend_schema(
        summary="Change transaction status",
        description="Change the status of a transaction (PROCESSED, REJECTED, REVERSED).",
        request=TransactionStatusSerializer,
        tags=['Transactions']
    )
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        transaction = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'transaction': transaction})
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        
        if new_status == 'PROCESSED':
            transaction.process()
        elif new_status == 'REJECTED':
            transaction.reject()
        elif new_status == 'REVERSED':
            transaction.reverse()
        
        return Response({'message': f'Transaction status changed to {new_status}'})
    
    @extend_schema(
        summary="Make a deposit",
        description="Create a deposit transaction to an account.",
        request=DepositSerializer,
        tags=['Transactions']
    )
    @action(detail=False, methods=['post'])
    def deposit(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)


        account_number = serializer.validated_data['account_number']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        
        try:
            # Get the account
            account = SavingsAccount.objects.get(account_number=account_number)
            
            # Check if account is active
            if not account.is_active:
                return Response(
                    {'error': 'Account is not active'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create deposit transaction
            transaction = Transaction.objects.create(
                transaction_type='DEPOSIT',
                source_account=account,
                amount=amount,
                description=description,
                user=request.user,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                status='PENDING'
            )
            
            # Process the deposit
            transaction.process()
            
            return Response({
                'message': 'Deposit created successfully',
                'transaction_id': transaction.id,
                'new_balance': str(account.current_balance)
            }, status=status.HTTP_201_CREATED)
            
        except SavingsAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Deposit failed: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Implementation would create deposit transaction
        return Response({'message': 'Deposit created successfully'}, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="Make a withdrawal",
        description="Create a withdrawal transaction from an account.",
        request=WithdrawalSerializer,
        tags=['Transactions']
    )
    @action(detail=False, methods=['post'])
    def withdrawal(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Implementation would create withdrawal transaction
        return Response({'message': 'Withdrawal created successfully'}, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="Make a transfer",
        description="Create a transfer transaction between accounts.",
        request=TransferSerializer,
        tags=['Transactions']
    )
    @action(detail=False, methods=['post'])
    def transfer(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Implementation would create transfer transactions
        return Response({'message': 'Transfer created successfully'}, status=status.HTTP_201_CREATED)