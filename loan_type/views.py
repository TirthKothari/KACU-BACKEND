from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

from .models import LoanType
from .serializers import LoanTypeSerializer, LoanTypeListSerializer
from api.permissions import IsAdmin, IsAuthenticatedWithRole

logger = logging.getLogger(__name__)


class LoanTypeListView(generics.ListAPIView):
    """
    List all loan types.
    Accessible by all authenticated users.

    GET /loan-types/
    """

    queryset = LoanType.objects.all().select_related('created_by').order_by('-created_at')
    serializer_class = LoanTypeListSerializer
    permission_classes = [IsAuthenticated, IsAuthenticatedWithRole]

    def get_queryset(self):
        """
        Optionally filter by search query parameter.
        """
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Override list to provide custom response format.
        """
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)

            logger.info(f"User {request.user.id} retrieved {queryset.count()} loan types")

            return Response({'success': True, 'message': 'Loan types retrieved successfully', 'data': serializer.data, 'count': queryset.count()}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error listing loan types: {str(e)}")
            return Response({'success': False, 'message': 'Failed to retrieve loan types', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoanTypeCreateView(generics.CreateAPIView):
    """
    Create a new loan type.
    Only accessible by admins.

    POST /loan-types/create/
    """

    queryset = LoanType.objects.all()
    serializer_class = LoanTypeSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create a new loan type with proper error handling.
        """
        try:
            # Add created_by to the request data
            data = request.data.copy()
            data['created_by'] = request.user.id

            serializer = self.get_serializer(data=data)

            if not serializer.is_valid():
                logger.warning(f"Invalid loan type data from admin {request.user.id}: {serializer.errors}")
                return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            loan_type = serializer.save(created_by=request.user)

            logger.info(f"Admin {request.user.id} created loan type {loan_type.id}")

            return Response({'success': True, 'message': 'Loan type created successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)

        except DjangoValidationError as e:
            logger.error(f"Django validation error creating loan type: {str(e)}")
            return Response({'success': False, 'message': 'Validation error', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating loan type: {str(e)}")
            return Response({'success': False, 'message': 'Failed to create loan type', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoanTypeDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific loan type by ID.
    Accessible by all authenticated users.

    GET /loan-types/<id>/
    """

    queryset = LoanType.objects.all().select_related('created_by')
    serializer_class = LoanTypeSerializer
    permission_classes = [IsAuthenticated, IsAuthenticatedWithRole]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve loan type with custom response format.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)

            logger.info(f"User {request.user.id} retrieved loan type {instance.id}")

            return Response({'success': True, 'message': 'Loan type retrieved successfully', 'data': serializer.data}, status=status.HTTP_200_OK)

        except LoanType.DoesNotExist:
            logger.warning(f"Loan type not found for user {request.user.id}")
            return Response({'success': False, 'message': 'Loan type not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving loan type: {str(e)}")
            return Response({'success': False, 'message': 'Failed to retrieve loan type', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoanTypeUpdateView(generics.UpdateAPIView):
    """
    Update an existing loan type (full or partial update).
    Only accessible by admins.

    PUT /loan-types/<id>/update/
    PATCH /loan-types/<id>/update/
    """

    queryset = LoanType.objects.all()
    serializer_class = LoanTypeSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    lookup_field = 'pk'

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Full update of loan type.
        """
        partial = kwargs.pop('partial', False)

        try:
            instance = self.get_object()

            # Prepare data
            data = request.data.copy()
            if not partial:
                # For full update, maintain the original creator
                data['created_by'] = instance.created_by.id

            serializer = self.get_serializer(instance, data=data, partial=partial)

            if not serializer.is_valid():
                logger.warning(f"Invalid update data from admin {request.user.id}: {serializer.errors}")
                return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            loan_type = serializer.save()

            update_type = "partially updated" if partial else "updated"
            logger.info(f"Admin {request.user.id} {update_type} loan type {loan_type.id}")

            return Response({'success': True, 'message': 'Loan type updated successfully', 'data': serializer.data}, status=status.HTTP_200_OK)

        except LoanType.DoesNotExist:
            logger.warning(f"Loan type not found for update by admin {request.user.id}")
            return Response({'success': False, 'message': 'Loan type not found'}, status=status.HTTP_404_NOT_FOUND)
        except DjangoValidationError as e:
            logger.error(f"Django validation error updating loan type: {str(e)}")
            return Response({'success': False, 'message': 'Validation error', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating loan type: {str(e)}")
            return Response({'success': False, 'message': 'Failed to update loan type', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        """
        Partial update of loan type.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class LoanTypeDeleteView(generics.DestroyAPIView):
    """
    Delete a loan type.
    Only accessible by admins.

    DELETE /loan-types/<id>/delete/
    """

    queryset = LoanType.objects.all()
    serializer_class = LoanTypeSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    lookup_field = 'pk'

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """
        Delete loan type with custom response.
        """
        try:
            instance = self.get_object()
            loan_type_id = instance.id
            loan_type_name = instance.name

            instance.delete()

            logger.info(f"Admin {request.user.id} deleted loan type {loan_type_id} ({loan_type_name})")

            return Response({'success': True, 'message': f'Loan type "{loan_type_name}" deleted successfully'}, status=status.HTTP_200_OK)

        except LoanType.DoesNotExist:
            logger.warning(f"Loan type not found for deletion by admin {request.user.id}")
            return Response({'success': False, 'message': 'Loan type not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting loan type: {str(e)}")
            return Response({'success': False, 'message': 'Failed to delete loan type', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoanTypeActiveView(APIView):
    """
    Get all active loan types for dropdown/selection purposes.
    Accessible by all authenticated users.

    GET /loan-types/active/
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """
        Return simplified list of active loan types.
        """
        try:
            loan_types = LoanType.objects.all().values('id', 'name', 'rates', 'amount')

            return Response({'success': True, 'message': 'Active loan types retrieved successfully', 'data': list(loan_types)}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving active loan types: {str(e)}")
            return Response({'success': False, 'message': 'Failed to retrieve active loan types', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
