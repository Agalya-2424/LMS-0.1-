# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# from . import views
# from .views import staff_messages

# router = DefaultRouter()
# router.register(r'categories', views.CategoryViewSet, basename='category')
# router.register(r'courses', views.CourseViewSet, basename='course')
# router.register(r'staff', views.StaffViewSet, basename='staff')
# router.register(r'students', views.StudentViewSet, basename='student')
# router.register(r'assignments', views.AssignmentViewSet, basename='assignment')
# router.register(r'attendance', views.AttendanceViewSet, basename='attendance')
# router.register(r'progress', views.CourseProgressViewSet, basename='progress')

# urlpatterns = [
#     path('register/', views.register_user, name='register'),
#     path('register/staff/', views.register_staff, name='register-staff'),
#     path('getdata/', views.getdata, name='getdata'),
#     path('user/role/', views.get_user_role, name='get-user-role'),
#     path('users/', views.get_all_users, name='get-all-users'),
    
#     # Dashboard stats
#     path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
#     path('staff/dashboard-stats/', views.staff_dashboard_stats, name='staff-dashboard-stats'),
#     path('student/dashboard-stats/', views.student_dashboard_stats, name='student-dashboard-stats'),
#     path('student/dashboard-stats/<int:student_id>/', views.student_dashboard_stats, name='student-dashboard-stats-detail'),
    
#     # Dashboard data
#     path('staff/attendance-data/', views.staff_attendance_data, name='staff-attendance-data'),
#     path('staff/performance-data/', views.staff_performance_data, name='staff-performance-data'),
#     path('student/progress-data/', views.student_progress_data, name='student-progress-data'),
#     path('student/progress-data/<int:student_id>/', views.student_progress_data, name='student-progress-data-detail'),
#     path('student/attendance-data/', views.student_attendance_data, name='student-attendance-data'),
#     path('student/attendance-data/<int:student_id>/', views.student_attendance_data, name='student-attendance-data-detail'),
#     path('student/assignments/', views.student_assignments, name='student-assignments'),
#     path('student/assignments/<int:student_id>/', views.student_assignments, name='student-assignments-detail'),
    
#     # Messages
#     path('messages/', views.get_all_messages, name='get_all_messages'),
#     path('staff/messages/', staff_messages, name='staff_messages'),
    
#     # Enrollment
#     path('enroll/', views.enroll_course, name='enroll'),
    
#     # Contact
#     path('contact/submit/', views.submit_contact, name='submit_contact'),
    
#     # JWT Auth
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
#     # Router URLs
#     path('', include(router.urls)),
    
#     path("enrollments/", views.enrollment_list, name="enrollment-list"),
# ]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .views import (staff_messages,  StaffAssignmentAPIView,
    StaffAssignmentDetailAPIView,
    StudentAssignmentAPIView,
    AssignmentSubmissionAPIView,
    StaffQuizAPIView, StaffQuizDetailAPIView,
    QuizQuestionAPIView, QuizQuestionDetailAPIView,
    QuizOptionAPIView, QuizOptionDetailAPIView,
    StudentQuizAPIView,
    StaffLiveClassAPIView, StaffLiveClassDetailAPIView,
    LiveClassAttendanceAPIView, StudentLiveClassAPIView
)
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'staff', views.StaffViewSet, basename='staff')
router.register(r'students', views.StudentViewSet, basename='student')
router.register(r'assignments', views.AssignmentViewSet, basename='assignment')
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')
router.register(r'progress', views.CourseProgressViewSet, basename='progress')

urlpatterns = [
    # User Register
    path('register/', views.register_user, name='register'),
    path('register/staff/', views.register_staff, name='register-staff'),
    path('getdata/', views.getdata, name='getdata'),
    path('user/role/', views.get_user_role, name='get-user-role'),
    # path('users/', views.get_all_users, name='get-all-users'),
    path("users/",  views.get_all_users),
    # Dashboard Stats
    path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
    path('staff/dashboard-stats/', views.staff_dashboard_stats, name='staff-dashboard-stats'),
    path('student/dashboard-stats/', views.student_dashboard_stats, name='student-dashboard-stats'),
    path('student/dashboard-stats/<int:student_id>/', views.student_dashboard_stats, name='student-dashboard-stats-detail'),

    # Dashboard Data
    path('staff/attendance-data/', views.staff_attendance_data, name='staff-attendance-data'),
    path('staff/performance-data/', views.staff_performance_data, name='staff-performance-data'),
    path('student/progress-data/', views.student_progress_data, name='student-progress-data'),
    path('student/progress-data/<int:student_id>/', views.student_progress_data, name='student-progress-data-detail'),
    path('student/attendance-data/', views.student_attendance_data, name='student-attendance-data'),
    path('student/attendance-data/<int:student_id>/', views.student_attendance_data, name='student-attendance-data-detail'),
    path('student/assignments/', views.StudentAssignmentAPIView.as_view(), name='student-assignments'),
    path('student/assignments/<int:id>/', views.StudentAssignmentAPIView.as_view(), name='student-assignments-detail'),

    path("student/assignments/", StudentAssignmentAPIView.as_view()),
    path("assignments/submit/", AssignmentSubmissionAPIView.as_view()),
    
    # Staff Assignments
    path('staff/assignments/', StaffAssignmentAPIView.as_view(), name='staff-assignments'),
    path('staff/assignments/<int:id>/', StaffAssignmentDetailAPIView.as_view(), name='staff-assignments-detail'),
    
    # Staff Quizzes
    path('staff/quizzes/', StaffQuizAPIView.as_view(), name='staff-quizzes'),
    path('staff/quizzes/<int:id>/', StaffQuizDetailAPIView.as_view(), name='staff-quizzes-detail'),
    path('staff/quizzes/questions/', QuizQuestionAPIView.as_view(), name='quiz-questions'),
    path('staff/quizzes/questions/<int:id>/', QuizQuestionDetailAPIView.as_view(), name='quiz-questions-detail'),
    path('staff/quizzes/options/', QuizOptionAPIView.as_view(), name='quiz-options'),
    path('staff/quizzes/options/<int:id>/', QuizOptionDetailAPIView.as_view(), name='quiz-options-detail'),
    
    # Student Quizzes
    path('student/quizzes/', StudentQuizAPIView.as_view(), name='student-quizzes'),
    
    # Staff Live Classes
    path('staff/live-classes/', StaffLiveClassAPIView.as_view(), name='staff-live-classes'),
    path('staff/live-classes/<int:id>/', StaffLiveClassDetailAPIView.as_view(), name='staff-live-classes-detail'),
    path('staff/live-classes/<int:live_class_id>/attendance/', LiveClassAttendanceAPIView.as_view(), name='live-class-attendance'),
    
    # Student Live Classes
    path('student/live-classes/', StudentLiveClassAPIView.as_view(), name='student-live-classes'),

    path('messages/', views.get_all_messages, name='get_all_messages'),
    path('staff/messages/', staff_messages, name='staff_messages'),

    # Enrollment
    path('enroll/', views.enroll_course, name='enroll'),                  # POST only
    path('enrollments/', views.enrollment_list, name='enrollment-list'),  # GET only
    

    # Contact
    path('contact/submit/', views.submit_contact, name='submit_contact'),
    path('settings/', views.site_settings, name='site-settings'),

    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Router Registered URLs
    path('', include(router.urls)),
]
