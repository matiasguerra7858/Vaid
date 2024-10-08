from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from djoser.social.views import ProviderAuthView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .models import UserAccount as User
from rest_framework.permissions import AllowAny  
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Sum
from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from .models import Organization, Person, Image
from .serializers import *
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.core.mail import send_mail
from .serializers import GuestSerializer
from rest_framework.parsers import MultiPartParser, FormParser
import os

class SubscribeNewsletterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = NewsletterSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            subscription, created = NewsletterSubscription.objects.get_or_create(email=email)
            if created:
                return Response({'message': 'Subscribed successfully'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'Email already subscribed'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PersonOrganizationDetailsDeleteView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def delete(self, request, *args, **kwargs):
        person_id = kwargs.get('person_id')
        organization_id = kwargs.get('organization_id')

        try:
            detail = PersonOrganizationDetails.objects.get(Person_id=person_id, Organization_id=organization_id)
            detail.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PersonOrganizationDetails.DoesNotExist:
            return Response({'error': 'Details not found'}, status=status.HTTP_404_NOT_FOUND)
                           

class ApplyOrgView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, user_id, org_id):
        try:

            if not user_id or not org_id:
                return Response(
                    {'error': 'user_id and org_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = User.objects.get(id=user_id)
            organization = Organization.objects.get(id=org_id)
            person = Person.objects.get(User=user)

            candidate, created = Candidate.objects.get_or_create(Person=person, Organization=organization)

            if created:
                return Response(
                    {'message': 'Candidate successfully added to the organization!'},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'message': 'Already applied to this organization.'},
                    status=status.HTTP_200_OK
                )

        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Person.DoesNotExist:
            return Response(
                {'error': 'Person not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error applying to organization: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserFormView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, user_id):
        try:
            data = request.data
            user = User.objects.get(id=user_id)
            person = Person.objects.get(User=user)
            
            person.date_of_birth = data.get('dateOfBirth')
            person.profession = data.get('profession')
            person.experience = data.get('experience')
            person.street_name = data.get('street')
            person.city = data.get('city')
            person.available_days = data.get('availableDays')
            person.available_times = data.get('availableTimes')
            person.modality = data.get('modality')
            person.topics = data.get('topics')
            person.goals = data.get('goals')
            person.motivations = data.get('motivations')
            person.save()

            user.is_form = True
            user.save()
            return Response({'message': 'Form data saved successfully!'}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RetrieveOrganizationExtView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            organization = Organization.objects.get(id=user_id)
            
            return Response(
                {'name': organization.name,
                 'description':organization.description,
                 'country':organization.country,
                 'userId':organization.User.id},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error retrieving organization: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RetrieveOrganizationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            organization = Organization.objects.get(User=user)
            
            return Response(
                {'id': organization.id,
                'name': organization.name,
                 'description':organization.description,
                 'country':organization.country},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error retrieving organization: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RetrieveUserOrganizations(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            person = Person.objects.get(User=user)
            organizations = Organization.objects.filter(personorganizationdetails__Person=person)
            organization_serializer = OrganizationSerializer(organizations, many=True)
            return Response(
                {'organizations': organization_serializer.data},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Person.DoesNotExist:
            return Response(
                {'error': 'Person not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error retrieving organizations: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RetrievePersonView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            person = Person.objects.get(User=user)
            person_serializer = PersonSerializer(person)
            user_serializer = UserSerializer(user) 
            return Response(
                {'person': person_serializer.data,
                 'user': user_serializer.data},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Person.DoesNotExist:
            return Response(
                {'error': 'Person not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error retrieving person: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        

class ApproveCandidate(APIView):
    permission_classes = [AllowAny]

    def post(self, request, candidate_id):
        try:
            candidate = Candidate.objects.get(id=candidate_id)
            person = candidate.Person
            organization = candidate.Organization

            # Crear PersonOrganizationDetails
            PersonOrganizationDetails.objects.create(Person=person, Organization=organization)

            # Eliminar el candidato
            candidate.delete()

            return Response({'message': 'Candidate approved and added to organization'}, status=status.HTTP_200_OK)
        except Candidate.DoesNotExist:
            return Response({'error': 'Candidate not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RejectCandidate(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, candidate_id):
        try:
            candidate = Candidate.objects.get(id=candidate_id)
            candidate.delete()

            return Response({'message': 'Candidate rejected and deleted'}, status=status.HTTP_200_OK)
        except Candidate.DoesNotExist:
            return Response({'error': 'Candidate not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrgView(generics.ListAPIView):
    
    permission_classes = [AllowAny]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

class CandidateDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, organization_id):
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

        candidates = Candidate.objects.filter(Organization=organization)
        serializer = CandidateDetailSerializer(candidates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RetrieveImageOrgView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            user_id = request.query_params.get('user_id')
            if not user_id:
                return Response(
                    {'error': 'User ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            organization = Organization.objects.get(id=user_id) 
            images = Image.objects.filter(User=organization.User)

            if images.exists():
                images_serializer = ImageSerializer(images, many=True)
                return Response(
                    {'images': images_serializer.data},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'No images found for the specified user'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error retrieving image: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RetrieveImageView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        try:
    
            user_id = request.query_params.get('user_id')
            if not user_id:
                return Response(
                    {'error': 'User ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = User.objects.get(id=user_id)
            images = Image.objects.filter(User=user)

            if images.exists():
                images_serializer = ImageSerializer(images, many=True)
                return Response(
                    {'images': images_serializer.data},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'No images found for the specified user'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error retrieving image: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UploadImageView(APIView):

    permission_classes = [AllowAny]
    def post(self, request):
        try:
            data = self.request.data
            user_id = data.get('user_id')                
            user = User.objects.get(id=user_id) 

            image = data['image']
            
            Image.objects.create(
                    image = image,
                    User = user
                )
            
            return Response(
                    {'success': 'Image Uploaded Successfully'},
                    status=status.HTTP_201_CREATED

                )
        except:
            return Response(
                {'error': 'Error Uploading Image'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                
            )


class CreatePerson(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            user_id = data.get('user_id')
            user = User.objects.get(id=user_id)
            
            person = Person(
                phone_number=data.get('phone_number'),
                country=data.get('country'),
                description=data.get('description'),
                User=user  # Usuario obtenido por ID
            )
            person.save()

            return Response({'message': 'Person created successfully'}, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreateOrganization(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        try:
            data = request.data
            

            user_id = data.get('user_id')
            if not user_id:
                return Response({'error': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Crear la organización
            organization = Organization(
                name=data.get('name'),
                description=data.get('description'),
                country=data.get('country'),
                website=data.get('website', ''),
                User=user
            )
            organization.save()

            return Response({'message': 'Organization created successfully'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# @method_decorator(csrf_exempt, name='dispatch')
class UserTypeUpdate(APIView):
    permission_classes = [AllowAny]  
    def patch(self, request, pk):
        try:
            data = json.loads(request.body)
            user = User.objects.get(pk=pk)
            user_type = data.get('user_type')
            is_completed = data.get('is_completed')

            if user_type is not None:
                user.user_type = user_type 
            if is_completed is not None:
                user.is_completed = is_completed

            user.save()
            return JsonResponse({'message': 'User updated successfully'}, status=200)
        except User.DoesNotExist:
            raise Http404("User not found")
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class CheckAttendanceAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, event_id, user_id):
        event = get_object_or_404(Event, id=event_id)
        user = get_object_or_404(UserAccount, id=user_id)
        
        # Verificar si la persona ya está registrada como asistente
        if EventPersonDetails.objects.filter(Event=event, Person__User=user).exists():
            return Response({'is_attending': True}, status=200)
        else:
            return Response({'is_attending': False}, status=200)

class CheckUserType(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id, *args, **kwargs):
        try:
            user = User.objects.get(id=user_id)
            return Response({'user_type': user.user_type})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

class CheckCompleteView(APIView):
    permission_classes = [AllowAny]  

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            return Response({'is_completed': user.is_completed})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

class CustomProviderAuthView(ProviderAuthView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 201:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )
            response.set_cookie(
                'refresh',
                refresh_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )
            response.set_cookie(
                'refresh',
                refresh_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')
        print(refresh_token)
        if refresh_token:
            request.data['refresh'] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get('access')

            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response


class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        access_token = request.COOKIES.get('access')

        if access_token:
            request.data['token'] = access_token

        return super().post(request, *args, **kwargs)


class LogoutView(APIView): 
    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access')
        response.delete_cookie('refresh')

        return response


# tasksViews
class TaskListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            organization = Organization.objects.get(id=pk)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

        tasks = Task.objects.filter(Organization=organization)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    def post(self, request, pk):
        
        try:
            organization = Organization.objects.get(id=pk)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data['Organization'] = organization.id  # Asociar la tarea a la organización obtenida de la URL

        serializer = TaskSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskUpdateDestroyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            task = Task.objects.get(id=pk)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TaskSerializer(task)
        return Response(serializer.data)
        

    def put(self, request, pk):
        try:
            task = Task.objects.get(id=pk)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        
        serializer = TaskSerializer(task, data=data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            task = Task.objects.get(id=pk)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class OrganizationMembersView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, organization_id, *args, **kwargs):
        organization = get_object_or_404(Organization, id=organization_id)
        
        person_org_details = PersonOrganizationDetails.objects.filter(Organization=organization)
        members = [details.Person for details in person_org_details]
        
        serializer = PersonSerializer(members, many=True)
        return Response(serializer.data)

class EventListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            organization = Organization.objects.get(id=pk)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

        events = Event.objects.filter(Organization=organization)
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    #Se puede postear un evento a la vez ya que, sino gernera erro en la linea 550
    def post(self, request, pk):
        try:
            organization = Organization.objects.get(id=pk)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data['Organization'] = organization.id # Asociar la tarea a la organización obtenida de la URL

        serializer = EventSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class EventUpdateDestroyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            event = Event.objects.get(id=pk)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = EventSerializer(event)
        return Response(serializer.data)
        

    def put(self, request, pk):
        try:
            event = Event.objects.get(id=pk)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        
        serializer = EventSerializer(event, data=data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            event = Event.objects.get(id=pk)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, organization_id):
        organization = get_object_or_404(Organization, id=organization_id)
        tags = Tag.objects.filter(Organization=organization)
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)

    def post(self, request, organization_id):
        print(request.data)
        organization = get_object_or_404(Organization, id=organization_id)
        data = request.data.copy()
        data['Organization'] = organization.id
        serializer = TagSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TagDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, organization_id, pk):
        return get_object_or_404(Tag, pk=pk, Organization_id=organization_id)

    def get(self, request, organization_id, pk):
        tag = self.get_object(organization_id, pk)
        serializer = TagSerializer(tag)
        return Response(serializer.data)

    def put(self, request, organization_id, pk):
        tag = self.get_object(organization_id, pk)
        data = request.data.copy()
        data['Organization'] = organization_id
        serializer = TagSerializer(tag, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, organization_id, pk):
        tag = self.get_object(organization_id, pk)
        tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PersonTagsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            # Obtener todas las etiquetas asociadas a la persona y eliminar duplicados
            person_tags = PersonTagDetails.objects.filter(Person__id=user_id).values('Tag').distinct()
            tag_ids = [detail['Tag'] for detail in person_tags]

            # Obtener las instancias de las etiquetas basadas en los IDs
            tags = Tag.objects.filter(id__in=tag_ids)

            # Serializar las etiquetas
            serializer = TagSerializer(tags, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, user_id):
        person = get_object_or_404(Person, id=user_id)
        data = request.data.copy()
        data['person'] = person.id

        serializer = AssignTagsToPersonSerializer(data=data)
        if serializer.is_valid():
            tags = serializer.validated_data['tags']
            for tag_id in tags:
                tag = get_object_or_404(Tag, id=tag_id)
                PersonTagDetails.objects.create(Person=person, Tag=tag)

            return Response({'message': 'Tags assigned successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, user_id):
        tag_id = request.query_params.get('tag_id')
        if not tag_id:
            return Response({'error': 'Tag ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            person_tag = PersonTagDetails.objects.filter(Person__id=user_id, Tag__id=tag_id)
            person_tag.delete()
            return Response({'message': 'Tag deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except PersonTagDetails.DoesNotExist:
            return Response({'error': 'Tag not found for this user'}, status=status.HTTP_404_NOT_FOUND)


class HeadquarterListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, organization_id):
        headquarters = Headquarter.objects.filter(Organization__id=organization_id)
        serializer = HeadquarterSerializer(headquarters, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, organization_id):
        organization = get_object_or_404(Organization, pk=organization_id)  # Obtener la instancia de la organización

        data = request.data.copy()  # Hacer una copia de los datos enviados
        data['Organization'] = organization.id  # Asignar la organización al diccionario de datos

        #No se repita el nombre de la sede
        if Headquarter.objects.filter(name=request.data['name']).exists():
            return Response({'error': 'Headquarter with the same name already exists'}, status=status.HTTP_400_BAD_REQUEST)    

        serializer = HeadquarterSerializer(data=data)
        if serializer.is_valid():
            headquarter = serializer.save(Organization=organization) 
            Inventory.objects.create(Headquarter=headquarter)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HeadquarterDetailUpdateDestroyView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, organization_id, pk):
        return get_object_or_404(Headquarter, pk=pk, Organization_id=organization_id)

    def get(self, request, organization_id, pk):
        headquarter = self.get_object(organization_id, pk)
        serializer = HeadquarterSerializer(headquarter)
        return Response(serializer.data)

    def put(self, request, organization_id, pk):
        headquarter = self.get_object(organization_id, pk)
        serializer = HeadquarterSerializer(headquarter, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, organization_id, pk):
        headquarter = self.get_object(organization_id, pk)
        headquarter.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        
        #No se repita el nombre del producto
        if Product.objects.filter(name=request.data['name']).exists():
            return Response({'error': 'Product with the same name already exists'}, status=status.HTTP_400_BAD_REQUEST)


        if serializer.is_valid():
            product = serializer.save()
            return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return Response({"message": "Product deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class ProductForHeadquarterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, headquarter_id):
        data = request.data
        # Intentar obtener el inventario asociado al headquarter
        try:
            inventory = Inventory.objects.get(Headquarter_id=headquarter_id)
        except Inventory.DoesNotExist:
            return Response({'error': 'Inventory for specified headquarter not found'}, status=status.HTTP_404_NOT_FOUND)

        # Obtener el producto del request
        product_id = data.get('Product')
        
        # Verificar si ya existe un registro en ProductInventoryDetails con el mismo producto e inventario
        try:
            product_inventory_details = ProductInventoryDetails.objects.get(Product_id=product_id, Inventory=inventory)
            # Si existe, actualizar la cantidad
            product_inventory_details.cuantity += int(data.get('cuantity', 0))
            product_inventory_details.save()
            return Response(ProductInventoryDetailsSerializer(product_inventory_details).data, status=status.HTTP_200_OK)
        except ProductInventoryDetails.DoesNotExist:
            # Si no existe, crear un nuevo registro
            data['Inventory'] = inventory.id
            serializer = ProductInventoryDetailsSerializer(data=data)
            
            if serializer.is_valid():
                product_inventory_details = serializer.save()
                return Response(ProductInventoryDetailsSerializer(product_inventory_details).data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, headquarter_id):
        
        try:
            inventory = Inventory.objects.get(Headquarter_id=headquarter_id)
        except Inventory.DoesNotExist:
            return Response({'error': 'Inventory for specified headquarter not found'}, status=status.HTTP_404_NOT_FOUND)
            
        product_inventory_details = ProductInventoryDetails.objects.filter(Inventory=inventory)
        serializer = ProductInventoryDetailsSerializer(product_inventory_details, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationHistoryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, organization_id):
        try:
            # Verificar que la organización existe
            organization = Organization.objects.get(id=organization_id)

            # Filtrar el historial de acciones de la ONG usando el campo headquarter_id
            history_records = History.objects.filter(Organization=organization)
            serializer = HistorySerializer(history_records, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, organization_id):
        serializer = HistorySerializer(data=request.data)
        print(request.data)
        print(serializer)
        if serializer.is_valid():

            # Verificar que el usuario y la sede existen
            try:
                organization = Organization.objects.get(id=organization_id)

                # Crear el historial
                history = History.objects.create(
                    action=serializer.validated_data['action'],
                    description=serializer.validated_data['description'],
                    Organization=organization
                )

                return Response({'message': 'Action recorded successfully', 'id': history.id}, status=status.HTTP_201_CREATED)

            except UserAccount.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            except Headquarter.DoesNotExist:
                return Response({'error': 'Headquarter not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, organization_id, headquarter_id):
        headquarter = get_object_or_404(Headquarter, pk=headquarter_id, Organization_id=organization_id)
        inventory, created = Inventory.objects.get_or_create(Headquarter=headquarter)
        
        category_name = request.data.get('Category')

        category, created = ProductCategory.objects.get_or_create(name=category_name)
        
        request.data['Category'] = category.id
        
        product_serializer = ProductSerializer(data=request.data)
        
        if product_serializer.is_valid():
            product = product_serializer.save()

            product_inventory_details = ProductInventoryDetails.objects.create(
                Product=product,
                Inventory=inventory,
                cuantity=request.data.get('quantity', 0)
            )

            return Response(ProductInventoryDetailsSerializer(product_inventory_details).data, status=status.HTTP_201_CREATED)
        
        else:
            print('Errores del serializador:', product_serializer.errors)
        
        return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#PROBRAR LA FUNCONES DE ABAJO(Si funciona el query_params y en postman. Sino cambia pasando el user_id por parametro en la url)

class EventAttendanceView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        event_id = request.query_params.get('event_id')

        try:
            event = Event.objects.get(id=event_id)
            list = EventPersonDetails.objects.filter(Event=event)
            serializers = EventPersonSerializer(list, many=True)
            return Response(serializers.data, status=status.HTTP_200_OK)

        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)


    def post(self, request):
        person_id = request.query_params.get('person_id')
        event_id = request.query_params.get('event_id')

        try:
            person = Person.objects.get(id=person_id)
            event = Event.objects.get(id=event_id)

            # Verificar si ya está registrado
            if EventPersonDetails.objects.filter(Person=person, Event=event).exists():
                return Response({'error': 'Person is already attending this event'}, status=status.HTTP_400_BAD_REQUEST)

            event_person_details = EventPersonDetails.objects.create(Person=person, Event=event)
            serializer = EventPersonSerializer(event_person_details)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        person_id = request.query_params.get('person_id')
        event_id = request.query_params.get('event_id')

        try:
            person = Person.objects.get(id=person_id)
            event = Event.objects.get(id=event_id)

            try:
                event_person_details = EventPersonDetails.objects.get(Person=person, Event=event)
                event_person_details.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            except EventPersonDetails.DoesNotExist:
                return Response({'error': 'Person is not attending this event'}, status=status.HTTP_404_NOT_FOUND)

        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)


class CreateInvitationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        event_id = request.query_params.get('event_id')

        try:
            event = Event.objects.get(id=event_id)

            if Invitation.objects.filter(Event=event).exists():
                return Response({'error': 'Invitation is already attending this event'}, status=status.HTTP_400_BAD_REQUEST)

            invitation = Invitation.objects.create(Event=event, status=True)
            serializer = InvitedEventSerializer(invitation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)


class CheckMembershipView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user_id = request.query_params.get('person_id')
        event_id = request.query_params.get('event_id')


        try:
            person = Person.objects.get(id=user_id)
            event = Event.objects.get(id=event_id)
            organization = Organization.objects.get(id=event.Organization.id)

            if PersonOrganizationDetails.objects.filter(Person= person, Organization = organization).exists():
                return Response({'is_member': True, 'event_id': event.id}, status=status.HTTP_200_OK)
            return Response({'is_member': False, 'event_id': event.id}, status=status.HTTP_403_FORBIDDEN)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)


class TaskParticipationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
            person_id = request.query_params.get('person_id')
            task_id = request.query_params.get('task_id')

            if not person_id or not task_id:
                return Response({'error': 'person_id and task_id are required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(id=person_id)
                task = Task.objects.get(id=task_id)
                person = Person.objects.get(User=user)

                # Verificar si la persona ya está asignada a la tarea
                is_taken = TaskPersonDetails.objects.filter(Person=person, Task=task).exists()
                print(f'{person} {is_taken} {user} {task}')
                
                return Response({'is_taken': is_taken}, status=status.HTTP_200_OK)

            except Person.DoesNotExist:
                return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
            except Task.DoesNotExist:
                return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)


    def post(self, request):
        person_id = request.query_params.get('person_id')
        task_id = request.query_params.get('task_id')

        if not person_id or not task_id:
            return Response({'error': 'person_id and task_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=person_id)
            task = Task.objects.get(id=task_id)
            person = Person.objects.get(User=user)

            if TaskPersonDetails.objects.filter(Person=person, Task=task).exists():
                return Response({'error': 'Person is already assigned to this task'}, status=status.HTTP_400_BAD_REQUEST)

            # Crear la instancia de TaskPersonDetails
            task_person_details = TaskPersonDetails.objects.create(Person=person, Task=task)
            return Response({'message': 'Task taken successfully', 'task_person_details': TaskPersonDetailsSerializer(task_person_details).data}, status=status.HTTP_201_CREATED)

        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        person_id = request.query_params.get('person_id')
        task_id = request.query_params.get('task_id')

        try:
            user = User.objects.get(id=person_id)
            task = Task.objects.get(id=task_id)
            person = Person.objects.get(User=user)

            try:
                task_person_details = TaskPersonDetails.objects.get(Person=person, Task=task)
                task_person_details.delete()
                return Response({'message': 'Task left successfully'}, status=status.HTTP_204_NO_CONTENT)

            except TaskPersonDetails.DoesNotExist:
                return Response({'error': 'Person is not assigned to this task'}, status=status.HTTP_404_NOT_FOUND)

        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

# Se epera en body un atributo denominado products, con la lista de ids de los productos comprados o vendidos
# "products": [
#         {
#             "product": 1,
#             "quantity": 10
#         }
#         {
#             "product": 6, (id del producto)
#             "quantity": 10
#         }
#     ]
class OperationAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, organization_id, operation_id=None):
        if operation_id:
            operation = get_object_or_404(Operation, id=operation_id, Organization_id=organization_id)
            serializer = OperationSerializer(operation)
            return Response(serializer.data)
        else:
            operations = Operation.objects.filter(Organization_id=organization_id)
            serializer = OperationSerializer(operations, many=True)
            return Response(serializer.data)

    def post(self, request, organization_id):
        print(request.data)
        request.data['Organization'] = organization_id
        serializer = OperationSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, organization_id, operation_id):
        operation = get_object_or_404(Operation, id=operation_id, Organization_id=organization_id)
        
        if operation.invoice:
            operation.invoice.delete()

        operation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OperationTypeListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = OperationType.objects.all()
    serializer_class = OperationTypeSerializer


class InventoryView(APIView):
    permission_classes = [AllowAny]
    # Obtener productos de una organización específica con la cantidad total
    def get(self, request, organization_id):
        # Filtramos los inventarios pertenecientes a la organización
        inventory_ids = Inventory.objects.filter(Headquarter__Organization_id=organization_id).values_list('id', flat=True)

        # Anotamos los productos con la suma total de las cantidades
        products = Product.objects.filter(
            productinventorydetails__Inventory_id__in=inventory_ids
        ).annotate(total_quantity=Sum('productinventorydetails__cuantity')).distinct()

        # Serializamos los productos con la cantidad total
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


# Product, Headquarter_1, Headquarter_2, quantity
class ProductTransferAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        product_id = request.query_params.get('product_id')
        headquarter1_id = request.query_params.get('headquarter1_id')
        headquarter2_id = request.query_params.get('headquarter2_id')
        quantity = request.query_params.get('quantity')

        if not product_id or not headquarter1_id or not headquarter2_id or not quantity:
            return Response({'error': 'product_id, headquarter1_id, headquarter2_id and quantity are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
            headquarter1 = Headquarter.objects.get(id=headquarter1_id)
            headquarter2 = Headquarter.objects.get(id=headquarter2_id)

                # Verificar si el producto está disponible en el inventario de la sede 1
            product_inventory_details = ProductInventoryDetails.objects.get(Product=product, Inventory=headquarter1.inventory)
            if product_inventory_details.cuantity < int(quantity):
                return Response({'error': 'Not enough quantity in headquarter 1'}, status=status.HTTP_400_BAD_REQUEST)


                # Actualizar las cantidades en los inventarios
            product_inventory_details.cuantity -= int(quantity)
            product_inventory_details.save()

            product_inventory_details2, created = ProductInventoryDetails.objects.get_or_create(Product=product, Inventory=headquarter2.inventory)
            product_inventory_details2.cuantity += int(quantity)
            product_inventory_details2.save()

            return Response({'message': 'Product transferred successfully'}, status=status.HTTP_201_CREATED)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        except Headquarter.DoesNotExist:
            return Response({'error': 'Headquarter not found'}, status=status.HTTP_404_NOT_FOUND)
        except ProductInventoryDetails.DoesNotExist:
            return Response({'error': 'Product not found in headquarter 1'}, status=status.HTTP_404_NOT_FOUND)


#Se debera poder agregar/eliminar miembros de un evento.
class MemberEventsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        event_id = request.query_params.get('event_id')

        try:
            event = Event.objects.get(id=event_id)
            members = EventPersonDetails.objects.filter(Event=event)
            serializer = EventPersonDetailsSerializer(members, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        
    def post(self, request):
        person_id = request.query_params.get('person_id')
        event_id = request.query_params.get('event_id')

        if not person_id or not event_id:
            return Response({'error': 'person_id and event_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            person = Person.objects.get(id=person_id)
            event = Event.objects.get(id=event_id)

            if EventPersonDetails.objects.filter(Person=person, Event=event).exists():
                return Response({'error': 'Person is already attending this event'}, status=status.HTTP_400_BAD_REQUEST)

            event_person_details = EventPersonDetails.objects.create(Person=person, Event=event)
            return Response({'message': 'Person added successfully', 'event_person_details': EventPersonDetailsSerializer(event_person_details).data}, status=status.HTTP_201_CREATED)

        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        
    def delete(self, request):
        person_id = request.query_params.get('person_id')
        event_id = request.query_params.get('event_id')

        try:
            person = Person.objects.get(id=person_id)
            event = Event.objects.get(id=event_id)

            try:
                event_person_details = EventPersonDetails.objects.get(Person=person, Event=event)
                event_person_details.delete()
                return Response({'message': 'Person removed successfully'}, status=status.HTTP_204_NO_CONTENT)

            except EventPersonDetails.DoesNotExist:
                return Response({'error': 'Person is not attending this event'}, status=status.HTTP_404_NOT_FOUND)

        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

    
#Se debera poder agregar/eliminar invitados a un evento con la class Guest.
class GuestEventsAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(request.data)
        event_id = request.data.get('event_id')
        print(f"Received event_id: {event_id}")

        if not event_id:
            return Response({'error': 'event_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(id=event_id)
            print(f"Event found: {event}")

            # Excluye 'Event' de los datos que se pasarán al serializador, ya que lo estamos manejando manualmente
            guest_data = {
                'name': request.data.get('name'),
                'email': request.data.get('email'),
                'role': request.data.get('role'),
                'Event': event_id 
            }
            print(f"Guest data: {guest_data}")

            # Crea el invitado sin pasar el campo 'Event'
            serializer = GuestSerializer(data=guest_data)

            if serializer.is_valid():
                guest = serializer.save(Event=event)
                print(f"Guest added!")
                return Response({'message': 'Guest added successfully', 'guest': GuestSerializer(guest).data}, status=status.HTTP_201_CREATED)

            # Si el serializador no es válido, imprimir los errores
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        
    def delete(self, request):
        guest_id = request.query_params.get('guest_id')

        if not guest_id:
            return Response({'error': 'guest_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            guest = Guest.objects.get(id=guest_id)
            guest.delete()
            return Response({'message': 'Guest removed successfully'}, status=status.HTTP_204_NO_CONTENT)

        except Guest.DoesNotExist:
            return Response({'error': 'Guest not found'}, status=status.HTTP_404_NOT_FOUND)
        
"""
se espera un body similar a este:{
    "description": "Donation description",
    "date": "2024-08-20",
    "products": [
        {
            "product": 1,
            "quantity": 10
        }
        {
            "product": 6, (id del producto)
            "quantity": 10
        }
    ]
}
"""
class DonationAPIView(APIView):
    permission_classes = [AllowAny]
#Hace falta que se vean los detalles de la donacions
    def get(self, request):
        org_id = request.query_params.get('org_id')
        
        if not org_id:
            return Response({'error': 'org_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        organization = Organization.objects.get(id=org_id)
        donations = Donation.objects.filter(Organization=organization)
        serializer = DonationSerializer(donations, many=True)
        return Response(serializer.data)

    def post(self, request):
        print(request.data)
        org_id = request.query_params.get('org_id')

        if not org_id:
            return Response({'error': 'org_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        organization = get_object_or_404(Organization, id=org_id)
        data = request.data.copy()
        data['Organization'] = organization.id
        serializer = DonationSerializer(data=data)

        if serializer.is_valid():
            donation = serializer.save()
            return Response(DonationSerializer(donation).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   
class DonationDetailAPIView(APIView):
    permission_classes = [AllowAny]
    # Obtener, actualizar o eliminar una donación específica
    def get(self, request):
        org_id = request.query_params.get('org_id')
        donation_id = request.query_params.get('donation_id')

        if not org_id or not donation_id:
            return Response({'error': 'org_id and donation_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        donation = get_object_or_404(Donation, id=donation_id, Organization_id=org_id)
        serializer = DonationSerializer(donation)
        return Response(serializer.data)

    def put(self, request):
        org_id = request.query_params.get('org_id')
        donation_id = request.query_params.get('donation_id')

        if not org_id or not donation_id:
            return Response({'error': 'org_id and donation_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        donation = get_object_or_404(Donation, id=donation_id, Organization_id=org_id)
        serializer = DonationSerializer(donation, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        org_id = request.query_params.get('org_id')
        donation_id = request.query_params.get('donation_id')

        if not org_id or not donation_id:
            return Response({'error': 'org_id and donation_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        donation = get_object_or_404(Donation, id=donation_id, Organization_id=org_id)
        donation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

#Se debe crear una view que permita enviar las invitaciones por mail 
"""
Se espera un body similar a este:
{
  "emails": ["galleguillolucas2006@gmail.com"],
  "event_id": 1,
  "subject": "Estás Invitado a Nuestro Evento",
  "link": "https://www.google.com"
}
Les desea mucha suerte galle :) <3
"""
class SendInvitationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        emails = request.data.get('emails') 
        event_id = request.data.get('event_id')  
        subject = request.data.get('subject', 'Invitación a Evento')
        link = request.data.get('link')  
        event = Event.objects.get(id=event_id)
        organization = event.Organization.name

        # Validar que los campos obligatorios están presentes
        if not emails or not event or not organization or not link:
            return Response({'error': 'emails, event and link are required fields.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            message_template = f"Hola,\n\nEstás invitado(a) a nuestro evento '{event.name}' que se llevará a cabo próximamente.\nEsperamos contar con tu presencia.\n{link}\n\nSaludos cordiales,\nEl equipo de {organization}"

            send_mail(
                subject=subject,  # Asunto del correo
                message=message_template,  # Contenido del mensaje personalizado
                from_email=settings.DEFAULT_FROM_EMAIL,  # Dirección de correo del remitente
                recipient_list=emails,  # Lista de destinatarios
                fail_silently=False,  # Generar excepción si falla el envío
            )
            print(f"Invitaciones enviadas exitosamente a: {', '.join(emails)}")
            return Response({'message': 'Invitations sent successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       

class SendInvitationPlatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        emails = [request.data.get('email')] 
        subject = 'You are invited to our platform!'
        organization_id = request.data.get('org_id')
        organization = Organization.objects.get(id=organization_id) 
        link = f'http://localhost:3000/dashboard/organization/{organization_id}'
        # Validar que los campos obligatorios están presentes
        if not emails or not organization or not link:
            return Response({'error': 'emails, and link are required fields.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            message_template = f"Hello,\n\nYou have been invited to join our platform and become a part of the organization: '{organization.name}'.\nWe look forward to your participation.\n{link}\n\nBest regards,\nThe Vaid Team"
            send_mail(
                subject=subject,  # Asunto del correo
                message=message_template,  # Contenido del mensaje personalizado
                from_email=settings.DEFAULT_FROM_EMAIL,  # Dirección de correo del remitente
                recipient_list=emails,  # Lista de destinatarios
                fail_silently=False,  # Generar excepción si falla el envío
            )
            print(emails)
            return Response({'message': 'Invitations sent successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


#View para subir un video al perfil de una organizacion

class VideoUploadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = self.request.data
            org_id = data.get('organization_id')
            organization = Organization.objects.get(id=org_id)

            video_file = data.get('video_file')
            title = data.get('title')
            description = data.get('description', 'Video content')

            Video.objects.create(
                title=title,
                description=description,
                video_file=video_file,
                Organization=organization
            )

            return Response(
                {'success': 'Video Uploaded Successfully'},
                status=status.HTTP_201_CREATED
            )
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error Uploading Video: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class IsAdminView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user_id = request.query_params.get('user_id')

        try:
            # Buscar el usuario primero
            user = User.objects.get(id=user_id)

            # Obtener la instancia de Person relacionada con el usuario
            person = Person.objects.get(User=user)

            # Filtrar las etiquetas del usuario usando la relación persontagdetails
            tags_user = Tag.objects.filter(persontagdetails__Person=person, isAdmin=True)  # Usar isAdmin en lugar de TagType

            if tags_user.exists():
                return Response(True, status=status.HTTP_200_OK)
            return Response(False, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
    

class UnassignedTagsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        # Obtener la persona
        person = get_object_or_404(Person, id=user_id)
        
        # Obtener IDs de las tags asignadas al usuario
        assigned_tag_ids = PersonTagDetails.objects.filter(Person=person).values_list('Tag', flat=True)
        
        if assigned_tag_ids.exists():
            # Obtener las tags que no están asignadas al usuario si existen etiquetas asignadas
            unassigned_tags = Tag.objects.exclude(id__in=assigned_tag_ids).distinct()
        else:
            # Si no hay etiquetas asignadas, obtener todas las etiquetas
            unassigned_tags = Tag.objects.all().distinct()

        # Serializar y devolver las tags
        serializer = TagSerializer(unassigned_tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AllProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, organization_id):
        # Verificamos que la organización existe
        organization = get_object_or_404(Organization, id=organization_id)

        # Obtenemos todos los IDs de inventarios asociados a la organización
        inventory_ids = Inventory.objects.filter(Headquarter__Organization=organization).values_list('id', flat=True)

        # Obtenemos los productos asociados a esos inventarios, agrupados por sede y sumando la cantidad total
        products = Product.objects.filter(
            productinventorydetails__Inventory_id__in=inventory_ids
        ).annotate(total_quantity=Sum('productinventorydetails__cuantity')).distinct()

        # Serializamos los productos
        serializer = ProductSerializer(products, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class EventDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, organization_id, event_id):
        event = get_object_or_404(Event, id=event_id, Organization_id=organization_id)
        serializer = EventSerializer(event)
        return Response(serializer.data, status=200)
    
    
class TaskDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, organization_id, task_id):
        task = get_object_or_404(Task, id=task_id, Organization_id=organization_id)
        serializer = TaskSerializer(task)
        return Response(serializer.data, status=200)


class MarkTaskAsDoneView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
            task.state = 'Done'  # Cambia el estado de la tarea
            task.save()
            return Response({"message": "Task marked as done successfully"}, status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)


class MarkTaskAsPendingView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
            task.state = 'Pending'  # Cambia el estado de la tarea a Pending
            task.save()
            return Response({"message": "Task marked as pending successfully"}, status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)


class EventGuestsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, event_id):
        try:
            # Obtén los invitados del evento por el ID del evento
            guests = Guest.objects.filter(Event_id=event_id)
            serializer = GuestSerializer(guests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Guest.DoesNotExist:
            return Response({'error': 'No guests found for this event.'}, status=status.HTTP_404_NOT_FOUND)


class EventParticipantsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        event_id = request.query_params.get('event_id')
        if not event_id:
            return Response({'error': 'event_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Obtener todas las relaciones de personas para el evento
        event_person_details = EventPersonDetails.objects.filter(Event_id=event_id)

        if not event_person_details.exists():
            return Response({'error': 'No participants found for this event.'}, status=status.HTTP_404_NOT_FOUND)

        # Obtener las personas relacionadas con el evento
        persons = [details.Person for details in event_person_details]

        # Serializar los datos de las personas
        serialized_persons = PersonSerializer(persons, many=True).data

        return Response(serialized_persons, status=status.HTTP_200_OK)

class DeleteGuestView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, guest_id, *args, **kwargs):
        try:
            guest = Guest.objects.get(id=guest_id)  # Asegúrate de usar el modelo 'Guest'
            guest.delete()
            return Response({"message": "Guest deleted successfully"}, status=status.HTTP_200_OK)
        except Guest.DoesNotExist:
            return Response({"error": "Guest not found"}, status=status.HTTP_404_NOT_FOUND)

class DeleteMemberView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, member_id, *args, **kwargs):
        try:
            member = EventPersonDetails.objects.get(id=member_id)
            member.delete()
            return Response({"message": "Member deleted successfully"}, status=status.HTTP_200_OK)
        except EventPersonDetails.DoesNotExist:
            return Response({"error": "Member not found"}, status=status.HTTP_404_NOT_FOUND)

class DeleteEventView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, event_id, *args, **kwargs):
        try:
            event = Event.objects.get(id=event_id)  # Busca el evento por su ID
            event.delete()  # Elimina el evento
            return Response({"message": "Event deleted successfully"}, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)


class FinishEventView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, event_id, *args, **kwargs):
        try:
            event = Event.objects.get(id=event_id)
            event.state = 'Done'  # Cambiar el estado a 'Done'
            event.save()
            return Response({"message": "Event finished successfully"}, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

class ToggleEventStateView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, event_id, *args, **kwargs):
        try:
            event = Event.objects.get(id=event_id)
            if event.state == 'Done':
                event.state = 'Pending'  # Cambia el estado a "Pending" si estaba "Done"
            else:
                event.state = 'Done'  # Cambia el estado a "Done" si estaba en otro estado
            event.save()
            return Response({"message": f"Event state changed to {event.state}", "state": event.state}, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

class EventToggleAttendanceAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, event_id, user_id):
        # Obtener el usuario y la persona correspondiente
        user = get_object_or_404(User, id=user_id)
        person = get_object_or_404(Person, User=user)
        event = get_object_or_404(Event, id=event_id)

        # Verificar si la persona ya está registrada en el evento
        try:
            event_person_detail = EventPersonDetails.objects.get(Person=person, Event=event)
            # Si existe, significa que ya está asistiendo, entonces lo removemos (leave)
            event_person_detail.delete()
            return Response({"message": "User has left the event."}, status=status.HTTP_200_OK)
        except EventPersonDetails.DoesNotExist:
            # Si no existe, lo registramos como asistente (join)
            EventPersonDetails.objects.create(Person=person, Event=event)
            return Response({"message": "User is now attending the event."}, status=status.HTTP_201_CREATED)


class UploadProfileImageView(APIView):
    
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        user = get_object_or_404(UserAccount, id=user_id)

        user_image = Image.objects.filter(User=user).first()

        if user_image and os.path.isfile(user_image.image.path):
            os.remove(user_image.image.path)
            user_image.delete()

        if 'file' not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        new_image = Image(User=user, image=request.FILES['file'], alt="Profile Image")
        new_image.save()

        image_url = request.build_absolute_uri(new_image.image.url)
        
        return Response({
            'message': 'Imagen de perfil actualizada correctamente',
            'image_url': image_url
        }, status=status.HTTP_201_CREATED)

