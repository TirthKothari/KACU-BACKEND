from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)


class BaseRolePermission(permissions.BasePermission):
    """
    Base permission class for role-based access control.
    Provides common functionality for role checking.
    """

    allowed_roles = []
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        """
        Check if user has permission to access the view.
        """
        try:
            # Check if user is authenticated
            if not request.user or not request.user.is_authenticated:
                self.message = "Authentication credentials were not provided."
                logger.warning(f"Unauthenticated access attempt to {view.__class__.__name__}")
                return False

            # Check if user has a valid role
            if not hasattr(request.user, 'role'):
                self.message = "User role is not defined."
                logger.error(f"User {request.user.id} does not have a role attribute")
                return False

            # Check if user's role is in allowed roles
            if request.user.role not in self.allowed_roles:
                self.message = f"Access denied. Required role(s): {', '.join(self.allowed_roles)}. Your role: {request.user.role}"
                logger.warning(f"User {request.user.id} with role {request.user.role} " f"attempted to access {view.__class__.__name__} which requires {self.allowed_roles}")
                return False

            return True

        except AttributeError as e:
            logger.error(f"AttributeError in permission check: {str(e)}")
            self.message = "Permission check failed due to missing user attributes."
            return False
        except Exception as e:
            logger.error(f"Unexpected error in permission check: {str(e)}")
            self.message = "An unexpected error occurred during permission verification."
            return False

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.
        Can be overridden in subclasses for specific object-level permissions.
        """
        return self.has_permission(request, view)


class IsAdmin(BaseRolePermission):
    """
    Permission class that allows access only to admin users.
    Admins have full access to all resources.
    """

    allowed_roles = ['ADMIN']
    message = "Only administrators can perform this action."


class IsApplicant(BaseRolePermission):
    """
    Permission class that allows access only to applicant users.
    Applicants can access their own loan applications and prequalification data.
    """

    allowed_roles = ['APPLICANT']
    message = "Only applicants can perform this action."

    def has_object_permission(self, request, view, obj):
        """
        Applicants can only access their own objects.
        """
        try:
            if not super().has_object_permission(request, view, obj):
                return False

            # Check if the object belongs to the user
            if hasattr(obj, 'user') and obj.user:
                if obj.user.id != request.user.id:
                    self.message = "You can only access your own data."
                    logger.warning(f"Applicant {request.user.id} attempted to access object belonging to user {obj.user.id}")
                    return False
                return True

            # If obj is the user itself
            if hasattr(obj, 'id') and obj.id == request.user.id:
                return True

            self.message = "Access denied to this resource."
            return False

        except Exception as e:
            logger.error(f"Error in IsApplicant object permission check: {str(e)}")
            self.message = "Permission verification failed."
            return False


class IsAgent(BaseRolePermission):
    """
    Permission class that allows access only to agent users.
    Agents can access applicants assigned to them.
    """

    allowed_roles = ['AGENT']
    message = "Only agents can perform this action."

    def has_object_permission(self, request, view, obj):
        """
        Agents can access their assigned applicants' data.
        """
        try:
            if not super().has_object_permission(request, view, obj):
                return False

            # Check if the object is assigned to this agent
            if hasattr(obj, 'assigned_agent') and obj.assigned_agent:
                if obj.assigned_agent.id != request.user.id:
                    self.message = "You can only access data of applicants assigned to you."
                    logger.warning(f"Agent {request.user.id} attempted to access object assigned to agent {obj.assigned_agent.id}")
                    return False
                return True

            # If obj has a user with an assigned agent
            if hasattr(obj, 'user') and obj.user and hasattr(obj.user, 'assigned_agent'):
                if obj.user.assigned_agent and obj.user.assigned_agent.id == request.user.id:
                    return True
                self.message = "You can only access data of applicants assigned to you."
                return False

            # Allow agents to view unassigned objects (for assignment purposes)
            return True

        except Exception as e:
            logger.error(f"Error in IsAgent object permission check: {str(e)}")
            self.message = "Permission verification failed."
            return False


class IsPartner(BaseRolePermission):
    """
    Permission class that allows access only to partner users.
    Partners can access applicants who used their referral code.
    """

    allowed_roles = ['PARTNER']
    message = "Only partners can perform this action."

    def has_object_permission(self, request, view, obj):
        """
        Partners can access applicants referred by them.
        """
        try:
            if not super().has_object_permission(request, view, obj):
                return False

            # Check if the object is associated with this partner
            if hasattr(obj, 'partner') and obj.partner:
                if obj.partner.id != request.user.id:
                    self.message = "You can only access data of applicants referred by you."
                    logger.warning(f"Partner {request.user.id} attempted to access object associated with partner {obj.partner.id}")
                    return False
                return True

            # Check if object has a reference code matching partner's reference code
            if hasattr(obj, 'refernce_code') and obj.refernce_code:
                if obj.refernce_code == request.user.reference_code:
                    return True

            self.message = "You can only access data of applicants referred by you."
            return False

        except Exception as e:
            logger.error(f"Error in IsPartner object permission check: {str(e)}")
            self.message = "Permission verification failed."
            return False


class IsAdminOrApplicant(BaseRolePermission):
    """
    Permission class that allows access to admin or applicant users.
    Useful for views where both admins and applicants can perform actions.
    """

    allowed_roles = ['ADMIN', 'APPLICANT']
    message = "Only administrators or applicants can perform this action."

    def has_object_permission(self, request, view, obj):
        """
        Admins have full access, applicants can only access their own objects.
        """
        try:
            if not super().has_object_permission(request, view, obj):
                return False

            # Admins have unrestricted access
            if request.user.role == 'ADMIN':
                return True

            # Applicants can only access their own data
            if request.user.role == 'APPLICANT':
                if hasattr(obj, 'user') and obj.user:
                    if obj.user.id != request.user.id:
                        self.message = "You can only access your own data."
                        return False
                    return True

                if hasattr(obj, 'id') and obj.id == request.user.id:
                    return True

                self.message = "Access denied to this resource."
                return False

            return False

        except Exception as e:
            logger.error(f"Error in IsAdminOrApplicant object permission check: {str(e)}")
            self.message = "Permission verification failed."
            return False


class IsAdminOrAgent(BaseRolePermission):
    """
    Permission class that allows access to admin or agent users.
    Useful for views where both admins and agents can perform actions.
    """

    allowed_roles = ['ADMIN', 'AGENT']
    message = "Only administrators or agents can perform this action."

    def has_object_permission(self, request, view, obj):
        """
        Admins have full access, agents can access their assigned applicants.
        """
        try:
            if not super().has_object_permission(request, view, obj):
                return False

            # Admins have unrestricted access
            if request.user.role == 'ADMIN':
                return True

            # Agents can access their assigned applicants
            if request.user.role == 'AGENT':
                if hasattr(obj, 'assigned_agent') and obj.assigned_agent:
                    if obj.assigned_agent.id == request.user.id:
                        return True
                    self.message = "You can only access data of applicants assigned to you."
                    return False

                if hasattr(obj, 'user') and obj.user and hasattr(obj.user, 'assigned_agent'):
                    if obj.user.assigned_agent and obj.user.assigned_agent.id == request.user.id:
                        return True
                    self.message = "You can only access data of applicants assigned to you."
                    return False

                # Allow agents to view unassigned objects
                return True

            return False

        except Exception as e:
            logger.error(f"Error in IsAdminOrAgent object permission check: {str(e)}")
            self.message = "Permission verification failed."
            return False


class IsAdminOrPartner(BaseRolePermission):
    """
    Permission class that allows access to admin or partner users.
    Useful for views where both admins and partners can perform actions.
    """

    allowed_roles = ['ADMIN', 'PARTNER']
    message = "Only administrators or partners can perform this action."

    def has_object_permission(self, request, view, obj):
        """
        Admins have full access, partners can access their referred applicants.
        """
        try:
            if not super().has_object_permission(request, view, obj):
                return False

            # Admins have unrestricted access
            if request.user.role == 'ADMIN':
                return True

            # Partners can access their referred applicants
            if request.user.role == 'PARTNER':
                if hasattr(obj, 'partner') and obj.partner:
                    if obj.partner.id == request.user.id:
                        return True
                    self.message = "You can only access data of applicants referred by you."
                    return False

                if hasattr(obj, 'refernce_code') and obj.refernce_code:
                    if obj.refernce_code == request.user.reference_code:
                        return True

                self.message = "You can only access data of applicants referred by you."
                return False

            return False

        except Exception as e:
            logger.error(f"Error in IsAdminOrPartner object permission check: {str(e)}")
            self.message = "Permission verification failed."
            return False


class IsOwnerOrAdmin(BaseRolePermission):
    """
    Permission class that allows object owners and admins to access objects.
    Works for any object that has a user field.
    """

    allowed_roles = ['ADMIN', 'APPLICANT', 'AGENT', 'PARTNER']
    message = "You must be the owner or an administrator to perform this action."

    def has_object_permission(self, request, view, obj):
        """
        Allow access if user is admin or the owner of the object.
        """
        try:
            if not super().has_object_permission(request, view, obj):
                return False

            # Admins have full access
            if request.user.role == 'ADMIN':
                return True

            # Check if user is the owner
            if hasattr(obj, 'user') and obj.user:
                if obj.user.id == request.user.id:
                    return True

            # If obj is the user itself
            if hasattr(obj, 'id') and obj.id == request.user.id:
                return True

            self.message = "You can only access your own data."
            logger.warning(f"User {request.user.id} attempted unauthorized access to object")
            return False

        except Exception as e:
            logger.error(f"Error in IsOwnerOrAdmin object permission check: {str(e)}")
            self.message = "Permission verification failed."
            return False


class IsReadOnly(permissions.BasePermission):
    """
    Permission class that allows read-only access (GET, HEAD, OPTIONS).
    Useful for public endpoints that should only allow viewing.
    """

    message = "This endpoint is read-only."

    def has_permission(self, request, view):
        """
        Allow only safe methods.
        """
        return request.method in permissions.SAFE_METHODS


class IsAuthenticatedWithRole(BaseRolePermission):
    """
    Permission class that checks if user is authenticated and has a valid role.
    Allows all authenticated users with a defined role.
    """

    allowed_roles = ['ADMIN', 'APPLICANT', 'AGENT', 'PARTNER']
    message = "Authentication and a valid role are required."
