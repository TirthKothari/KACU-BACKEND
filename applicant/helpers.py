import secrets  # Use secrets for better randomness than 'random'

from django.db import IntegrityError, transaction


def generate_referral_code(length=5):
    # Alphabet without confusing characters
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(secrets.choice(chars) for _ in range(length))
    return f"LOAN-{code}"


def assign_agent_round_robin(applicant_user):
    """
    Assign an applicant to the next active agent using round-robin fairness.
    """
    # Import lazily to avoid circular import with models importing this module.
    from .models import AgentAssignmentState, User
    from .utils import UserRoleChoices

    with transaction.atomic():
        try:
            state = AgentAssignmentState.objects.select_for_update().get(pk=1)
        except AgentAssignmentState.DoesNotExist:
            try:
                AgentAssignmentState.objects.create(pk=1)
            except IntegrityError:
                # Another transaction created it first.
                pass
            state = AgentAssignmentState.objects.select_for_update().get(pk=1)

        eligible_agents = list(User.objects.filter(role=UserRoleChoices.AGENT.value, is_active=True).order_by('id'))

        if not eligible_agents:
            return None

        selected_agent = eligible_agents[0]

        if state.last_assigned_agent_id:
            for idx, agent in enumerate(eligible_agents):
                if agent.id == state.last_assigned_agent_id:
                    selected_agent = eligible_agents[(idx + 1) % len(eligible_agents)]
                    break

        applicant_user.assigned_agent = selected_agent
        applicant_user.save(update_fields=['assigned_agent'])

        state.last_assigned_agent = selected_agent
        state.save(update_fields=['last_assigned_agent', 'updated_at'])

        return selected_agent


def generate_registration_jwt(email, prequalification_uuid):
    """
    Generate a JWT token for applicant registration.
    """
    import jwt
    import datetime
    from django.conf import settings

    payload = {'email': email, 'prequalification_uuid': str(prequalification_uuid), 'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=getattr(settings, "JWT_TOKEN_EXPIRY_HOURS"))}
    key = getattr(settings, "JWT_KEY")
    token = jwt.encode(payload, key, algorithm=getattr(settings, "JWT_ALGORITHM"))
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


def verify_registration_jwt(token, email):
    """
    Decode and verify applicant registration JWT token.
    """
    import jwt
    from django.conf import settings

    try:
        payload = jwt.decode(token, getattr(settings, "JWT_KEY"), algorithms=[getattr(settings, "JWT_ALGORITHM")])
        if payload.get('email') != email:
            return False, "Email does not match the token payload."
        return True, "Token is valid"
    except jwt.ExpiredSignatureError:
        return False, "The registration link has expired."
    except jwt.InvalidTokenError:
        return False, "Invalid registration token."
