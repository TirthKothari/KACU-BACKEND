from django.contrib import admin
from .models import LoanType

# Register your models here.


@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'rates', 'decision_time', 'amount', 'description', 'created_at', 'updated_at', 'created_by')
    search_fields = ('name', 'description', 'created_by__username')
    list_filter = ('created_at', 'updated_at')
