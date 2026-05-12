from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils import timezone
from django.contrib import messages
from apps.authentication.models import AdminRequestModel
from django.db import transaction


@admin.action(description='Approve selected requests')
def approve_requests(modeladmin, request, queryset):    # TODO: remember to notify user after approval
    """
    Custom action — approves selected pending requests.
    Moves the user from 'viewer' group to 'admin' group.
    """
    admin_group, _ = Group.objects.get_or_create(name='admin')
    viewer_group   = Group.objects.get(name='viewer')

    approved_count = 0

    for admin_request in queryset:

        if admin_request.status != AdminRequestModel.Status.PENDING:
            continue

        with transaction.atomic():
            user = admin_request.user
            user.groups.remove(viewer_group)
            user.groups.add(admin_group)

            admin_request.status      = AdminRequestModel.Status.APPROVED
            admin_request.reviewed_at = timezone.now()
            admin_request.save()

            approved_count += 1

    modeladmin.message_user(
        request,
        f'{approved_count} request(s) approved successfully.',
        messages.SUCCESS
    )

@admin.action(description='Reject selected requests')
def reject_requests(modeladmin, request, queryset):     # TODO: remember to notify user after rejection
    """
    Custom action — rejects selected pending requests.
    User stays as viewer.
    """
    rejected_count = 0

    for admin_request in queryset:

        if admin_request.status != AdminRequestModel.Status.PENDING:
            continue

        with transaction.atomic():
            admin_request.status      = AdminRequestModel.Status.REJECTED
            admin_request.reviewed_at = timezone.now()
            admin_request.save()

            rejected_count += 1

    modeladmin.message_user(
        request,
        f'{rejected_count} request(s) rejected.',
        messages.WARNING
    )



@admin.register(AdminRequestModel)
class AdminRequestAdmin(admin.ModelAdmin):

    list_display = ('user', 'status', 'requested_at', 'reviewed_at')

    list_filter = ('status',)

    search_fields = ('user__username',)

    readonly_fields = ('user', 'requested_at', 'reviewed_at')

    actions = [approve_requests, reject_requests]


