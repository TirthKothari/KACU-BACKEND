from django.shortcuts import get_object_or_404
from loan_application.models import LoanApplication
from applicant.utils import UserRoleChoices
from .models import ChatRoom
from .utils import ChatRoomType


def is_application_chat_participant(user, loan_application):
    """
    Check whether a user is a valid participant of an application chat.

    Participants are:
      - The applicant (loan_application.user)
      - The applicant's partner (loan_application.user.partner)
      - The applicant's assigned agent (loan_application.user.assigned_agent)
      - Any admin
    """
    if user.role == UserRoleChoices.ADMIN.value:
        return True

    app_user = loan_application.user

    # Applicant themselves
    if app_user.id == user.id:
        return True

    # Partner
    if app_user.partner and app_user.partner.id == user.id:
        return True

    # Assigned agent
    if app_user.assigned_agent and app_user.assigned_agent.id == user.id:
        return True

    return False


def get_or_create_application_chat_room(loan_application, creator):
    """
    Return the existing ChatRoom for a LoanApplication, or create one.
    The room name defaults to the applicant's name + loan application UUID.
    """
    chat_room, created = ChatRoom.objects.get_or_create(
        loan_application=loan_application,
        defaults={
            'room_type': ChatRoomType.APPLICATION.value,
            'name': f"Application Chat – {loan_application.user.get_full_name()} ({loan_application.loan_application_uuid})",
            'created_by': creator,
        },
    )
    return chat_room


def get_loan_application_for_chat(loan_application_uuid, user):
    """
    Fetch a LoanApplication by UUID, enforcing participant access.
    Admins may access any application; others must be a participant.
    """
    if user.role == UserRoleChoices.ADMIN.value:
        return get_object_or_404(LoanApplication, loan_application_uuid=loan_application_uuid)

    loan_application = get_object_or_404(LoanApplication, loan_application_uuid=loan_application_uuid)

    if not is_application_chat_participant(user, loan_application):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("You are not a participant of this application chat.")

    return loan_application
