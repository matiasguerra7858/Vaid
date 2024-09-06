from django.urls import path, re_path
from .views import *

urlpatterns = [
    re_path(
        r'^o/(?P<provider>\S+)/$',
        CustomProviderAuthView.as_view(),
        name='provider-auth'
    ),

    path('person-organization-details/<int:person_id>/<int:organization_id>/delete/', PersonOrganizationDetailsDeleteView.as_view()),
    path('user/<int:user_id>/apply-org/<int:org_id>/', ApplyOrgView.as_view()),
    path('user/form/<int:user_id>/', UserFormView.as_view()),
    path('retrieve-logo-org', RetrieveImageOrgView.as_view()),
    path('organization-ext/<int:user_id>/', RetrieveOrganizationExtView.as_view()),
    path('organization/<int:user_id>/', RetrieveOrganizationView.as_view()),
    path('user/all-organizations/', OrgView.as_view()),
    path('user/<int:user_id>/organizations/', RetrieveUserOrganizations.as_view()),
    path('person/<int:user_id>/', RetrievePersonView.as_view()),
    path('candidate/<int:candidate_id>/approve/', ApproveCandidate.as_view()),
    path('candidate/<int:candidate_id>/reject/', RejectCandidate.as_view()),
    path('candidate-details/<int:organization_id>/', CandidateDetailView.as_view()),
    path('retrieve-logo', RetrieveImageView.as_view()),
    path('upload-image', UploadImageView.as_view()),
    path('user/<int:user_id>/check-usertype', CheckUserType.as_view()),
    path('user/person', CreatePerson.as_view()),
    path('user/organization', CreateOrganization.as_view()),
    path('user/<int:pk>/complete', UserTypeUpdate.as_view()),
    path('user/<int:user_id>/check-complete', CheckCompleteView.as_view()),
    path('jwt/create/', CustomTokenObtainPairView.as_view()),
    path('jwt/refresh/', CustomTokenRefreshView.as_view()),
    path('jwt/verify/', CustomTokenVerifyView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('organizations/<int:pk>/tasks/', TaskListView.as_view(), name='task-list'),
    path('organizations/tasks/<int:pk>', TaskUpdateDestroyView.as_view(), name='task-update-delete'),
    path('organizations/<int:organization_id>/members/', OrganizationMembersView.as_view(), name='organization-members'),
    path('organizations/<int:pk>/events/', EventListView.as_view(), name='event-list'),
    path('organizations/events/<int:pk>', EventUpdateDestroyView.as_view(), name='event-update-delete'),
    path('organizations/<int:organization_id>/tags/', TagListCreateAPIView.as_view(), name='tag-list-create'),
    path('organizations/<int:organization_id>/tags/<int:pk>/', TagDetailAPIView.as_view(), name='tag-detail'),
    path('user/<int:user_id>/tags/', PersonTagsAPIView.as_view(), name='tags-to-person'),
    path('headquarters/<int:organization_id>/', HeadquarterListCreateView.as_view(), name='headquarter-list'),
    path('headquarters/<int:organization_id>/edit/<int:pk>/', HeadquarterDetailUpdateDestroyView.as_view(), name='headquarter-update-delete'),
    path('products/', ProductView.as_view(), name='product-list'),
    path('headquarters/<int:headquarter_id>/products/', ProductForHeadquarterView.as_view(), name='product-headquarter'),
    path('organizations/<int:organization_id>/history/', OrganizationHistoryView.as_view(), name='organization-history'),
    path('products/<int:pk>/', ProductView.as_view(), name='product-detail-delete'),
    path('headquarters/<int:organization_id>/<int:headquarter_id>/products/', ProductCreateView.as_view(), name='add-product'),
    path('events/attendance/', EventAttendanceView.as_view(), name='event-attendance'),
    path('organizations/invitations/', CreateInvitationView.as_view(), name='create-invitation'),
    path('organizations/membership/', CheckMembershipView.as_view(), name='check-membership'),
    path('organizations/tasks/participation/', TaskParticipationView.as_view(), name='task-participation'),
    path('organization/<int:organization_id>/operation/', OperationAPIView.as_view(), name='operation-list-create'),
    path('organization/<int:organization_id>/operation/<int:operation_id>/', OperationAPIView.as_view(), name='operation-detail-delete'),
    path('organization/operation-type/', OperationTypeListView.as_view(), name='operation-type-list-create'),
    path('organization/<int:organization_id>/inventory', InventoryView.as_view(), name='inventory-list'),
    path('organization/transferProduct', ProductTransferAPIView.as_view(), name='transfer-list-create'),
    path('organization/event/members', MemberEventsAPIView.as_view(), name='event-members'),
    path('organization/event/guest', GuestEventsAPIView.as_view(), name='event-Guests'),
    path('donations/', DonationAPIView.as_view(), name='donation-create'),
    path('donation/detail/', DonationDetailAPIView.as_view(), name='donation-detail'),
    path('send-email/', SendInvitationView.as_view(), name='send-email'),
    path('<int:organization_id>/history/', OrganizationHistoryView.as_view()),
    path('organization/upload-video/', VideoUploadView.as_view(), name='upload-organization-video'),
    path('isAdmin/', IsAdminView.as_view(), name='is-admin'),
    path('user/<int:user_id>/unassigned-tags/', UnassignedTagsAPIView.as_view(), name='unassigned-tags'),
    path('send-email-plat/', SendInvitationPlatView.as_view()),
    path('organization/<int:organization_id>/all-products/', AllProductsView.as_view(), name='all-products'),
    path('organizations/<int:organization_id>/events/<int:event_id>/', EventDetailView.as_view(), name='event-detail'),
    path('organizations/<int:organization_id>/tasks/<int:task_id>/', TaskDetailView.as_view(), name='task-detail'),
    path('tasks/<int:task_id>/mark-as-done/', MarkTaskAsDoneView.as_view(), name='mark-task-as-done'),
    path('tasks/<int:task_id>/mark-as-pending/', MarkTaskAsPendingView.as_view(), name='mark-task-as-pending'),
]
