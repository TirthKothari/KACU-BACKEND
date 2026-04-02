from rest_framework import status, serializers, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from api import settings
from .serializers import PreQualificationSerializer, UserRegistrationSerializer
from .models import User, pre_qualification
from .helpers import assign_agent_round_robin
from .utils import UserRoleChoices
from django.db import transaction
import logging
from api.permissions import IsAdminOrApplicant, IsApplicant


logger = logging.getLogger(settings.LOGGER)


class CreatePrequalification(APIView):
    """
    API endpoint to create a prequalification form submission.
    Accepts POST request with form data, validates it, and stores in database.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        try:
            logger.info("Received prequalification form submission.")

            # Check if email exists in the request data
            email = request.data.get('email')

            if email:
                # Check if prequalification already exists with this email
                existing_prequalification = pre_qualification.objects.filter(email=email).first()

                if existing_prequalification:
                    # If no user is associated, inform that they already applied
                    if existing_prequalification.user is None:
                        logger.info(f"Email {email} already has a prequalification form with UUID: {existing_prequalification.uuid}")
                        return Response({'success': False, 'message': 'You have already applied for prequalification', 'form_uuid': str(existing_prequalification.uuid)}, status=status.HTTP_200_OK)
                    else:
                        # User already registered and associated
                        logger.warning(f"Email {email} already has a user account associated")
                        return Response(
                            {
                                'success': False,
                                'message': 'An account already exists with this email. Please login.',
                            },
                            status=status.HTTP_409_CONFLICT,
                        )

            serializer = PreQualificationSerializer(data=request.data)

            if serializer.is_valid():
                logger.debug("Prequalification form data is valid.")

                # Check annual revenue and set is_qualified
                annual_revenue = serializer.validated_data.get('annual_revenue', 0)
                is_qualified = annual_revenue > 15000
                logger.debug(f"Annual revenue: {annual_revenue}, is_qualified set to: {is_qualified}")

                instance = serializer.save(is_qualified=is_qualified)
                logger.info(f"Prequalification form submitted successfully with UUID: {instance.uuid}, is_qualified: {is_qualified}")

                return Response({'success': True, 'message': 'Prequalification form submitted successfully', 'form_uuid': str(instance.uuid), 'data': serializer.data}, status=status.HTTP_201_CREATED)
            else:
                logger.warning("Prequalification form data validation failed.")
                return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error processing prequalification form submission: {str(e)}", exc_info=True)
            return Response({'success': False, 'message': 'An error occurred while processing your request', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdatePrequalification(APIView):
    """
    API endpoint to update an existing prequalification form.
    Accepts PUT request with complete form data for full update.
    Only the user associated with the form or an admin can update it.
    """

    permission_classes = [IsAdminOrApplicant]  # Will implement custom logic inside

    def put(self, request, uuid):
        try:
            logger.info(f"Received prequalification form update request for UUID: {uuid}")

            # Get the prequalification form
            try:
                prequalification_form = pre_qualification.objects.get(uuid=uuid)
            except pre_qualification.DoesNotExist:
                logger.warning(f"Prequalification form not found with UUID: {uuid}")
                return Response({'success': False, 'message': 'Prequalification form not found'}, status=status.HTTP_404_NOT_FOUND)

            # Check permissions
            self.check_object_permissions(request, prequalification_form)

            if prequalification_form.is_qualified:
                logger.info(f"Prequalification form {uuid} is already qualified. No updates allowed.")
                return Response({'success': False, 'message': 'This prequalification form is already qualified and cannot be updated'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate and update the form
            serializer = PreQualificationSerializer(prequalification_form, data=request.data)

            if not serializer.is_valid():
                logger.warning(f"Prequalification form update validation failed for UUID: {uuid}")
                return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            # Check annual revenue and set is_qualified
            annual_revenue = serializer.validated_data.get('annual_revenue', 0)
            is_qualified = annual_revenue > 15000
            logger.debug(f"Updated annual revenue: {annual_revenue}, is_qualified set to: {is_qualified}")

            # Save with updated is_qualified
            updated_instance = serializer.save(is_qualified=is_qualified)

            # Update user's is_qualified if user exists
            if updated_instance.user:
                updated_instance.user.is_qualified = is_qualified
                updated_instance.user.save()
                logger.info(f"Updated user {updated_instance.user.id} is_qualified status to: {is_qualified}")

            logger.info(f"Prequalification form {uuid} updated successfully")

            return Response({'success': True, 'message': 'Prequalification form updated successfully', 'form_uuid': str(updated_instance.uuid), 'data': serializer.data}, status=status.HTTP_200_OK)

        except PermissionError as pe:
            logger.error(f"Permission denied for updating prequalification form {uuid}: {str(pe)}")
            return Response({'success': False, 'message': 'You do not have permission to update this prequalification form'}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            logger.error(f"Error updating prequalification form: {str(e)}", exc_info=True)
            return Response({'success': False, 'message': 'An error occurred while processing your request', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetPrequalification(generics.RetrieveAPIView):
    """
    API endpoint to retrieve a prequalification form by UUID.
    Returns the prequalification form data for authenticated users.
    """

    queryset = pre_qualification.objects.all()
    serializer_class = PreQualificationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'


class ApplicantUserRegistration(APIView):
    """
    API endpoint to register a new user and associate them with a prequalification form.
    Creates user and updates prequalification form atomically.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        try:
            logger.info("Received user registration request.")
            serializer = UserRegistrationSerializer(data=request.data)

            if not serializer.is_valid():
                logger.warning("User registration validation failed.")
                return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data

            try:
                with transaction.atomic():
                    # Get and update prequalification form
                    prequalification_form = pre_qualification.objects.get(uuid=validated_data['prequalification_form_uuid'])

                    if prequalification_form.user is not None:
                        logger.warning(f"Prequalification form {prequalification_form.uuid} already has a user assigned.")
                        raise serializers.ValidationError("This prequalification form is already associated with a user.")

                    # Create new user with email as username
                    user = User.objects.create_user(username=validated_data['email'], email=validated_data['email'], password=validated_data['password'], first_name=validated_data['first_name'], last_name=validated_data['last_name'], phone=validated_data['phone'], role=UserRoleChoices.APPLICANT.value, is_qualified=prequalification_form.is_qualified)

                    logger.info(f"User created successfully with username: {user.username}")

                    assigned_agent = assign_agent_round_robin(user)
                    if assigned_agent:
                        logger.info(f"Applicant {user.id} assigned to agent {assigned_agent.id}")
                    else:
                        logger.warning(f"No active agents available while registering applicant {user.id}")

                    # Associate user with prequalification form
                    prequalification_form.user = user
                    prequalification_form.save()
                    logger.info(f"Prequalification form {prequalification_form.uuid} updated with user {user.username}")

                    return Response(
                        {
                            'success': True,
                            'message': 'User registered successfully',
                            'data': {
                                'user_id': user.id,
                                'username': user.username,
                                'email': user.email,
                                'first_name': user.first_name,
                                'last_name': user.last_name,
                                'phone': user.phone,
                                'role': user.role,
                                'is_qualified': user.is_qualified,
                                'prequalification_form_uuid': str(prequalification_form.uuid),
                                'assigned_agent': (
                                    {
                                        'id': assigned_agent.id,
                                        'first_name': assigned_agent.first_name,
                                        'last_name': assigned_agent.last_name,
                                        'email': assigned_agent.email,
                                    }
                                    if assigned_agent
                                    else None
                                ),
                            },
                        },
                        status=status.HTTP_201_CREATED,
                    )

            except pre_qualification.DoesNotExist:
                logger.error(f"Prequalification form not found: {validated_data.get('prequalification_form_uuid')}")
                return Response({'success': False, 'message': 'Prequalification form not found'}, status=status.HTTP_404_NOT_FOUND)
            except serializers.ValidationError as ve:
                logger.error(f"Validation error: {str(ve)}")
                return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}", exc_info=True)
            return Response({'success': False, 'message': 'An error occurred while processing your request', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLoginView(APIView):
    """
    API endpoint for user login.
    Accepts POST request with username and password, authenticates user.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        try:
            logger.info("Received user login request.")

            username = request.data.get('username')
            password = request.data.get('password')

            # Validate input
            if not username or not password:
                logger.warning("Login attempt with missing credentials.")
                return Response({'success': False, 'message': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

            # Authenticate user
            user = authenticate(username=username, password=password)

            if user is not None:
                # Check if user is active
                if not user.is_active:
                    logger.warning(f"Login attempt for inactive user: {username}")
                    return Response({'success': False, 'message': 'User account is disabled'}, status=status.HTTP_403_FORBIDDEN)

                # Delete old token and create new one
                Token.objects.filter(user=user).delete()
                token = Token.objects.create(user=user)
                logger.info(f"User {user.username} logged in successfully. New token generated.")

                return Response({'success': True, 'message': 'Login successful', 'token': token.key, 'user': {'user_id': user.id, 'username': user.username, 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name, 'phone': user.phone, 'role': user.role, 'is_qualified': user.is_qualified}}, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Failed login attempt for username: {username}")
                return Response({'success': False, 'message': 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            logger.error(f"Error during user login: {str(e)}", exc_info=True)
            return Response({'success': False, 'message': 'An error occurred while processing your request', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RetrieveUserPrequalification(generics.RetrieveAPIView):
    """
    API endpoint to retrieve the prequalification form associated with the authenticated user.
    """

    serializer_class = PreQualificationSerializer
    permission_classes = [IsApplicant]

    def get_object(self):
        try:
            prequalification_form = pre_qualification.objects.get(user=self.request.user)
            return prequalification_form
        except pre_qualification.DoesNotExist:
            logger.warning(f"No prequalification form found for user {self.request.user.id}")
            raise serializers.ValidationError("No prequalification form found for this user.")
