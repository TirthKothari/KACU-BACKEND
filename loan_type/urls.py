from django.urls import path
from .views import (
    LoanTypeListView,
    LoanTypeCreateView,
    LoanTypeDetailView,
    LoanTypeUpdateView,
    LoanTypeDeleteView,
    LoanTypeActiveView,
)

urlpatterns = [
    # List all loan types (GET)
    path('', LoanTypeListView.as_view(), name='loan-type-list'),
    # Create new loan type (POST - Admin only)
    path('create/', LoanTypeCreateView.as_view(), name='loan-type-create'),
    # Get active loan types for dropdowns (GET)
    path('active/', LoanTypeActiveView.as_view(), name='loan-type-active'),
    # Retrieve single loan type (GET)
    path('<int:pk>/', LoanTypeDetailView.as_view(), name='loan-type-detail'),
    # Update loan type (PUT/PATCH - Admin only)
    path('<int:pk>/update/', LoanTypeUpdateView.as_view(), name='loan-type-update'),
    # Delete loan type (DELETE - Admin only)
    path('<int:pk>/delete/', LoanTypeDeleteView.as_view(), name='loan-type-delete'),
]
