from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets,permissions
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from .serializers import AssignmentSerializer,AssignmentSubmissionSerializer


from .models import (
    Category, Course, Staff, Student,
    Enrollment, ContactMessage, StaffMessage,
    Assignment, Attendance, CourseProgress, SiteSetting,AssignmentSubmission,
    Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAnswer,
    LiveClass, LiveClassAttendance
)

from .serializers import (
    CategorySerializer, CourseSerializer,
    ContactMessageSerializer, EnrollmentSerializer,
    StaffMessageSerializer, StaffSerializer,
    StudentSerializer, AssignmentSerializer,
    AttendanceSerializer, CourseProgressSerializer,
    SiteSettingSerializer,AssignmentSubmissionSerializer,
    QuizSerializer, QuizQuestionSerializer, QuizOptionSerializer,
    QuizAttemptSerializer, QuizAnswerSerializer,
    LiveClassSerializer, LiveClassAttendanceSerializer
)
from django.db.models import Avg, Sum
from django.utils import timezone


# ---------------------------- BASIC VIEWS ----------------------------
@api_view(['GET'])
def getdata(request):
    return Response({'name': 'Agalya', 'project': 'LMS'})


# ---------------------------- GET USER ROLE ----------------------------
@api_view(['GET'])
def get_user_role(request):
    """Get user role (admin, staff, student) based on logged in user - uses Django User model only"""
    if not request.user.is_authenticated:
        return Response({"error": "Not authenticated"}, status=401)
    
    user = request.user
    email = user.email or user.username
    
    # Check if user is admin (superuser/staff)
    if user.is_superuser or user.is_staff:
        role = "admin"
        user_id = user.id
    # Check if user exists in Staff table
    elif Staff.objects.filter(email=email).exists():
        staff = Staff.objects.get(email=email)
        role = "staff"
        user_id = staff.id
    else:
        # All other users are students (using Django User model, not Student model)
        role = "student"
        user_id = user.id
    
    return Response({
        "role": role,
        "username": user.username,
        "email": email,
        "user_id": user_id
    })


# ---------------------------- GET ALL USERS (FOR ADMIN) ----------------------------
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    """Get all Django Users for admin"""
    
    # Only admin can access
    if not (request.user.is_superuser or request.user.is_staff):
        return Response({"error": "Admin access required"}, status=403)

    users = User.objects.all().order_by('-date_joined')

    users_data = []
    for user in users:

        # Determine role
        if user.is_superuser or user.is_staff:
            role = "admin"
        elif Staff.objects.filter(email=user.email or user.username).exists():
            role = "staff"
        else:
            role = "student"

        # Name handling
        username_parts = user.username.split(' ') if user.username else []
        first_name = user.first_name or (username_parts[0] if username_parts else "-")
        last_name = user.last_name or (' '.join(username_parts[1:]) if len(username_parts) > 1 else "-")

        users_data.append({
            "id": user.id,
            "username": user.username,
            "email": user.email or "-",
            "first_name": first_name or "-",
            "last_name": last_name or "-",
            "role": role,
            "date_joined": user.date_joined,
            "last_login": user.last_login,
        })

    return Response(users_data)



@api_view(['POST'])
def submit_contact(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Contact form submitted!"}, status=201)
    return Response(serializer.errors, status=400)


@api_view(['GET'])
def get_all_messages(request):
    messages = ContactMessage.objects.all().order_by('-created_at')
    serializer = ContactMessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['GET', 'PUT'])
def site_settings(request):
    defaults = {
        "site_name": "SkillUp LMS",
        "theme_color": "#2563eb",
        "about": "Next-gen learning management system",
    }
    setting, _ = SiteSetting.objects.get_or_create(id=1, defaults=defaults)

    if request.method == 'GET':
        serializer = SiteSettingSerializer(setting)
        return Response(serializer.data)

    serializer = SiteSettingSerializer(setting, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


# ---------------------------- REGISTER USER ----------------------------
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
@api_view(['POST'])
@permission_classes([AllowAny]) 
def register_user(request):
    """Register new user - automatically creates as student (Django User only, not Student model)"""
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    confirm_password = request.data.get('confirmPassword')

    if not username or not email or not password:
        return Response({'error': 'All fields required'}, status=400)

    if password != confirm_password:
        return Response({'error': 'Passwords do not match'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username exists'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email exists'}, status=400)

    # Create user in Django User model (not Student model)
    # All registered users are automatically students by default
    user = User.objects.create_user(username=username, email=email, password=password)
    refresh = RefreshToken.for_user(user)

    return Response({
        'message': 'User registered as student',
        'role': 'student',  # All registered users are students
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_staff(request):
    """Register new staff member - creates Django User + Staff profile"""
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    confirm_password = request.data.get('confirmPassword')
    full_name = request.data.get('name') or username
    staff_role = request.data.get('role', '')

    if not username or not email or not password:
        return Response({'error': 'All fields required'}, status=400)

    if password != confirm_password:
        return Response({'error': 'Passwords do not match'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username exists'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email exists'}, status=400)

    # Create Django user (do not set is_staff to avoid admin routing)
    user = User.objects.create_user(username=username, email=email, password=password)

    # Create Staff profile
    Staff.objects.create(
        name=full_name or username,
        email=email,
        role=staff_role or ''
    )

    refresh = RefreshToken.for_user(user)

    return Response({
        'message': 'Staff registered successfully',
        'role': 'staff',
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    })
    

# ---------------------------- DASHBOARD STATS ----------------------------
# @api_view(['GET'])
# def dashboard_stats(request):
#     """Admin Dashboard Stats - uses Django User model for students count"""
#     # Count students: all users except admin/staff
#     total_students = User.objects.filter(is_superuser=False, is_staff=False).count()
    
#     data = {
#         "totalCourses": Course.objects.count(),
#         "totalStudents": total_students,  # Using Django User model
#         "totalStaff": Staff.objects.count(),
#         "totalEnrollments": Enrollment.objects.count(),
#     }
#     return Response(data)
@api_view(['GET'])
def dashboard_stats(request):
    """Admin Dashboard Stats - includes charts data"""

    # Students count from Django User model (except admin/staff)
    total_students = User.objects.filter(is_superuser=False, is_staff=False).count()

    # Weekly Activity (Last 7 days)
    today = timezone.now().date()
    from datetime import timedelta

    weekly_activity = []
    for i in range(7):
        day = today - timedelta(days=i)
        enrollments_count = Enrollment.objects.filter(enrolled_at__date=day).count()
        new_students_count = User.objects.filter(
            date_joined__date=day,
            is_superuser=False,
            is_staff=False
        ).count()

        weekly_activity.append({
            "day": day.strftime("%a"),
            "enrollments": enrollments_count,
            "students": new_students_count,
        })

    weekly_activity.reverse()

    # Course Distribution
    course_distribution = []
    categories = Category.objects.all()
    for cat in categories:
        course_distribution.append({
            "name": cat.name,
            "value": Course.objects.filter(category=cat).count()
        })

    data = {
        "totalCourses": Course.objects.count(),
        "totalStudents": total_students,
        "totalStaff": Staff.objects.count(),
        "totalEnrollments": Enrollment.objects.count(),

        "weekly_activity": weekly_activity,
        "course_distribution": course_distribution
    }

    return Response(data)



@api_view(['GET'])
def staff_dashboard_stats(request):
    """Staff Dashboard Stats - uses Django User model for students"""
    # Get total students (Django User model, not Student model)
    total_students = User.objects.filter(is_superuser=False, is_staff=False).count()
    
    # Calculate average attendance rate
    avg_attendance = Attendance.objects.aggregate(
        avg_percentage=Avg('percentage')
    )['avg_percentage'] or 0
    
    # Count total assignments/tasks
    total_tasks = Assignment.objects.count()
    completed_tasks = Assignment.objects.filter(is_completed=True).count()
    
    # Calculate average working hours (assuming 8 hours per day for 5 days)
    # This is a placeholder calculation - adjust based on your needs
    avg_hours = 7.4
    
    data = {
        "totalStudents": total_students,
        "attendanceRate": round(avg_attendance, 1),
        "tasksCompleted": completed_tasks,
        "avgWorkingHours": avg_hours,
    }
    return Response(data)


@api_view(['GET'])
def student_dashboard_stats(request, student_id=None):
    """Student Dashboard Stats - uses Django User model (not Student model)"""
    if not request.user.is_authenticated:
        return Response({"error": "Not authenticated"}, status=401)
    
    # Use logged in user directly (Django User model)
    user = request.user
    
    # If student_id provided, use that user (for admin viewing student)
    if student_id:
        try:
            user = User.objects.get(id=student_id, is_superuser=False, is_staff=False)
        except User.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)
    
    # Try to get Student record for enrollments/assignments (if exists)
    email = user.email or user.username
    student_record = None
    if Student.objects.filter(email=email).exists():
        student_record = Student.objects.get(email=email)
    
    # Count enrolled courses (using Student model for enrollments if exists)
    courses_enrolled = 0
    attendance_rate = 0
    completed_assignments = 0
    total_assignments = 0
    study_hours = 0
    
    if student_record:
        courses_enrolled = Enrollment.objects.filter(student=student_record).count()
        attendance_records = Attendance.objects.filter(student=student_record)
        attendance_rate = attendance_records.aggregate(
            avg_percentage=Avg('percentage')
        )['avg_percentage'] or 0
        completed_assignments = Assignment.objects.filter(student=student_record, is_completed=True).count()
        total_assignments = Assignment.objects.filter(student=student_record).count()
        progress_records = CourseProgress.objects.filter(student=student_record)
        total_progress = progress_records.aggregate(total=Sum('progress'))['total'] or 0
        study_hours = round(total_progress * 0.5, 1)
    
    # Calculate average grade
    avg_grade = "N/A"
    if total_assignments > 0:
        completion_rate = (completed_assignments / total_assignments) * 100
        if completion_rate >= 90:
            avg_grade = "A+"
        elif completion_rate >= 80:
            avg_grade = "A"
        elif completion_rate >= 70:
            avg_grade = "B+"
        elif completion_rate >= 60:
            avg_grade = "B"
        elif completion_rate >= 50:
            avg_grade = "C"
        else:
            avg_grade = "D"
    
    data = {
        "coursesEnrolled": courses_enrolled,
        "attendanceRate": round(attendance_rate, 1),
        "averageGrade": avg_grade,
        "studyHours": study_hours,
    }
    return Response(data)


# ---------------------------- ENROLLMENT ----------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def enroll_course(request):
    email = request.data.get('email')
    name = request.data.get('name')
    course_id = request.data.get('course')

    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)

    student, created = Student.objects.get_or_create(
        email=email,
        defaults={'name': name}
    )

    if Enrollment.objects.filter(student=student, course=course).exists():
        return Response({"message": "Already enrolled"}, status=200)

    enrollment = Enrollment.objects.create(student=student, course=course)
    serializer = EnrollmentSerializer(enrollment)

    return Response({"success": True, "data": serializer.data}, status=201)


# ---------------------------- CRUD VIEWSETS ----------------------------

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
              {"message": "Course deleted successfully"},
              status=status.HTTP_200_OK
    )
 


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer


class CourseProgressViewSet(viewsets.ModelViewSet):
    queryset = CourseProgress.objects.all()
    serializer_class = CourseProgressSerializer


# ---------------------------- STAFF MESSAGES ----------------------------
@api_view(['GET', 'POST'])
def staff_messages(request):

    if request.method == 'GET':
        messages = StaffMessage.objects.all().order_by('-created_at')
        serializer = StaffMessageSerializer(messages, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = StaffMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Staff message saved!"}, status=201)
        return Response(serializer.errors, status=400)


# ---------------------------- DASHBOARD DETAILS ----------------------------
@api_view(['GET'])
def staff_attendance_data(request):
    """Get attendance data for staff dashboard chart"""
    # Get last 5 months of attendance data
    attendance_records = Attendance.objects.all().order_by('-month')[:5]
    data = []
    
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    for idx, day in enumerate(days):
        avg_attendance = Attendance.objects.aggregate(
            avg=Avg('percentage')
        )['avg'] or 0
        # Vary slightly for visualization
        data.append({
            'day': day,
            'attendance': round(avg_attendance + (idx * 2 - 4), 1)
        })
    
    return Response(data)


@api_view(['GET'])
def staff_performance_data(request):
    """Get task performance data for staff dashboard"""
    total = Assignment.objects.count()
    completed = Assignment.objects.filter(is_completed=True).count()
    in_progress = Assignment.objects.filter(is_completed=False).count() - Assignment.objects.filter(is_completed=False, due_date__lt=timezone.now().date()).count()
    pending = Assignment.objects.filter(is_completed=False, due_date__gte=timezone.now().date()).count()
    
    data = [
        {"name": "Completed", "value": completed},
        {"name": "In Progress", "value": in_progress},
        {"name": "Pending", "value": pending},
    ]
    
    return Response(data)


@api_view(['GET'])
def student_progress_data(request, student_id=None):
    """Get course progress data for student dashboard - uses Django User model"""
    if not request.user.is_authenticated:
        return Response({"error": "Not authenticated"}, status=401)
    
    # Use logged in user (Django User model)
    user = request.user
    
    # If student_id provided, use that user (for admin viewing student)
    if student_id:
        try:
            user = User.objects.get(id=student_id, is_superuser=False, is_staff=False)
        except User.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)
    
    # Try to find matching Student record by email for enrollments/progress
    email = user.email or user.username
    student_record = None
    if Student.objects.filter(email=email).exists():
        student_record = Student.objects.get(email=email)
    
    data = []
    
    if student_record:
        progress_records = CourseProgress.objects.filter(student=student_record).select_related('course')
        
        for record in progress_records[:5]:  # Limit to 5 courses
            data.append({
                'name': record.course.title[:10] if len(record.course.title) > 10 else record.course.title,
                'progress': record.progress
            })
        
        # If no progress records, return enrollments
        if not data:
            enrollments = Enrollment.objects.filter(student=student_record).select_related('course')[:5]
            for enrollment in enrollments:
                data.append({
                    'name': enrollment.course.title[:10] if len(enrollment.course.title) > 10 else enrollment.course.title,
                    'progress': 0
                })
    
    return Response(data)


@api_view(['GET'])
def student_attendance_data(request, student_id=None):
    """Get attendance data for student dashboard - uses Django User model"""
    if not request.user.is_authenticated:
        return Response({"error": "Not authenticated"}, status=401)
    
    # Use logged in user (Django User model)
    user = request.user
    
    # If student_id provided, use that user (for admin viewing student)
    if student_id:
        try:
            user = User.objects.get(id=student_id, is_superuser=False, is_staff=False)
        except User.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)
    
    # Try to find matching Student record by email for attendance
    email = user.email or user.username
    student_record = None
    if Student.objects.filter(email=email).exists():
        student_record = Student.objects.get(email=email)
    
    base_attendance = 90  # Default
    
    if student_record:
        attendance_records = Attendance.objects.filter(student=student_record).order_by('-month')[:1]
        if attendance_records.exists():
            base_attendance = attendance_records.first().percentage
    
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    data = []
    for idx, day in enumerate(days):
        # Vary slightly around base attendance
        data.append({
            'day': day,
            'attendance': round(base_attendance + (idx * 1.5 - 3), 1)
        })
    
    return Response(data)

class StaffAssignmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if user is staff
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        # Assignment.staff is a User, not Staff
        assignments = Assignment.objects.filter(staff=request.user)
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Check if user is staff
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        serializer = AssignmentSerializer(data=request.data)
        if serializer.is_valid():
            # Assignment.staff is a User, so use request.user
            serializer.save(staff=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=400)

class StaffAssignmentDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, id):
        # Check if user is staff
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            # Assignment.staff is a User, not Staff
            assignment = Assignment.objects.get(id=id, staff=request.user)
        except Assignment.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        serializer = AssignmentSerializer(assignment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        # Check if user is staff
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            # Assignment.staff is a User, not Staff
            assignment = Assignment.objects.get(id=id, staff=request.user)
        except Assignment.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        assignment.delete()
        return Response({"message": "Assignment deleted"})

# -------------------------
# STUDENT VIEW + SUBMIT
# -------------------------
class StudentAssignmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Students can see all assignments from all staff
        assignments = Assignment.objects.all().order_by("-created_at")
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)


class AssignmentSubmissionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data["student"] = request.user.id

        serializer = AssignmentSubmissionSerializer(data=data)
        if serializer.is_valid():
            serializer.save(student=request.user)
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def enrollment_list(request):
    enrollments = Enrollment.objects.all()
    serializer = EnrollmentSerializer(enrollments, many=True)
    return Response(serializer.data)


# ---------------------------- QUIZ VIEWS ----------------------------
class StaffQuizAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if user is staff
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        quizzes = Quiz.objects.filter(staff=request.user).order_by('-created_at')
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Check if user is staff
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        serializer = QuizSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(staff=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)


class StaffQuizDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            quiz = Quiz.objects.get(id=id, staff=request.user)
        except Quiz.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        serializer = QuizSerializer(quiz)
        return Response(serializer.data)

    def put(self, request, id):
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            quiz = Quiz.objects.get(id=id, staff=request.user)
        except Quiz.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        serializer = QuizSerializer(quiz, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            quiz = Quiz.objects.get(id=id, staff=request.user)
        except Quiz.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        quiz.delete()
        return Response({"message": "Quiz deleted"})


class QuizQuestionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if user is staff
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        serializer = QuizQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)


class QuizQuestionDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, id):
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            question = QuizQuestion.objects.get(id=id)
            # Verify quiz belongs to staff
            if question.quiz.staff != request.user:
                return Response({"error": "Not authorized"}, status=403)
        except QuizQuestion.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        serializer = QuizQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            question = QuizQuestion.objects.get(id=id)
            if question.quiz.staff != request.user:
                return Response({"error": "Not authorized"}, status=403)
        except QuizQuestion.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        question.delete()
        return Response({"message": "Question deleted"})


class QuizOptionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        serializer = QuizOptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)


class QuizOptionDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, id):
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            option = QuizOption.objects.get(id=id)
            if option.question.quiz.staff != request.user:
                return Response({"error": "Not authorized"}, status=403)
        except QuizOption.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        serializer = QuizOptionSerializer(option, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            option = QuizOption.objects.get(id=id)
            if option.question.quiz.staff != request.user:
                return Response({"error": "Not authorized"}, status=403)
        except QuizOption.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        option.delete()
        return Response({"message": "Option deleted"})


class StudentQuizAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Students can see all quizzes
        quizzes = Quiz.objects.all().order_by('-created_at')
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)


# ---------------------------- LIVE CLASS VIEWS ----------------------------
class StaffLiveClassAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if user is staff
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        live_classes = LiveClass.objects.filter(staff=request.user).order_by('-scheduled_date')
        serializer = LiveClassSerializer(live_classes, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Check if user is staff
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        serializer = LiveClassSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(staff=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)


class StaffLiveClassDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            live_class = LiveClass.objects.get(id=id, staff=request.user)
        except LiveClass.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        serializer = LiveClassSerializer(live_class)
        return Response(serializer.data)

    def put(self, request, id):
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            live_class = LiveClass.objects.get(id=id, staff=request.user)
        except LiveClass.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        serializer = LiveClassSerializer(live_class, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        try:
            Staff.objects.get(email=request.user.email)
        except Staff.DoesNotExist:
            return Response({"error": "Staff only access"}, status=403)

        try:
            live_class = LiveClass.objects.get(id=id, staff=request.user)
        except LiveClass.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        live_class.delete()
        return Response({"message": "Live class deleted"})


class LiveClassAttendanceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, live_class_id):
        try:
            live_class = LiveClass.objects.get(id=live_class_id)
        except LiveClass.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        attendances = LiveClassAttendance.objects.filter(live_class=live_class)
        serializer = LiveClassAttendanceSerializer(attendances, many=True)
        return Response(serializer.data)

    def post(self, request, live_class_id):
        try:
            live_class = LiveClass.objects.get(id=live_class_id)
        except LiveClass.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        # Check if already attended
        attendance, created = LiveClassAttendance.objects.get_or_create(
            live_class=live_class,
            student=request.user,
            defaults={'joined_at': timezone.now()}
        )

        if not created:
            return Response({"message": "Already joined"}, status=200)

        serializer = LiveClassAttendanceSerializer(attendance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StudentLiveClassAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Students can see all live classes
        live_classes = LiveClass.objects.all().order_by('-scheduled_date')
        serializer = LiveClassSerializer(live_classes, many=True)
        return Response(serializer.data)