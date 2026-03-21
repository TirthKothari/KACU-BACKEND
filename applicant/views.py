from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from api import settings
from .serializers import PreQualificationSerializer, UserRegistrationSerializer
from .models import User, pre_qualification
from .utils import UserRoleChoices
from django.db import transaction
import logging


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

                    # Associate user with prequalification form
                    prequalification_form.user = user
                    prequalification_form.save()
                    logger.info(f"Prequalification form {prequalification_form.uuid} updated with user {user.username}")

                    return Response({'success': True, 'message': 'User registered successfully', 'data': {'user_id': user.id, 'username': user.username, 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name, 'phone': user.phone, 'role': user.role, 'is_qualified': user.is_qualified, 'prequalification_form_uuid': str(prequalification_form.uuid)}}, status=status.HTTP_201_CREATED)

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
