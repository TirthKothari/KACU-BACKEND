from django.contrib import admin
from .models import pre_qualification, User

# Register your models here.


admin.site.register(User)


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_qualified', 'partner', 'reference_code')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'partner__username')
    list_filter = ('role', 'is_qualified')


admin.site.register(pre_qualification)


class pre_qualificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'user', 'business_name', 'loan_amount', 'loan_type', 'loan_term', 'annual_revenue', 'is_qualified', 'name', 'email', 'phone', 'partner', 'created_at', 'updated_at')
    search_fields = ('business_name', 'user__username', 'loan_type', 'email', 'phone', 'partner__username')
    list_filter = ('is_qualified', 'loan_type', 'created_at', 'business_location')
    sortable_by = ('annual_revenue', 'loan_amount')
