from rest_framework import serializers
from .models import (
    ContactMessage, Category, Course,
    StaffMessage, Enrollment, Student, Staff,
    Assignment, Attendance, CourseProgress,  AssignmentSubmission,SiteSetting,
    Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAnswer,
    LiveClass, LiveClassAttendance
)


# ---------------- CONTACT MESSAGE ----------------
class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']


# ---------------- CATEGORY ----------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


# ---------------- COURSE ----------------
class CourseSerializer(serializers.ModelSerializer):
    # For GET → show category details
    category = CategorySerializer(read_only=True)

    # For POST → accept category_id or category (for compatibility)
    category_id = serializers.IntegerField(write_only=True, required=False)

    image = serializers.ImageField(use_url=True, required=False)

    class Meta:
        model = Course
        fields = "__all__"

    def create(self, validated_data):
        # Handle both category_id and category (as int from form)
        if "category_id" in validated_data:
            category_id = validated_data.pop("category_id")
        elif "category" in validated_data:
            category_id = validated_data.pop("category")
        else:
            raise serializers.ValidationError("category_id or category is required")
        
        validated_data["category"] = Category.objects.get(id=category_id)
        return Course.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Handle both category_id and category (as int from form)
        if "category_id" in validated_data:
            category_id = validated_data.pop("category_id")
            instance.category = Category.objects.get(id=category_id)
        elif "category" in validated_data:
            category_id = validated_data.pop("category")
            instance.category = Category.objects.get(id=category_id)
        return super().update(instance, validated_data)


# ---------------- STUDENT ----------------
class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"


# ---------------- STAFF ----------------
class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = "__all__"


# ---------------- ENROLLMENT ----------------
class EnrollmentSerializer(serializers.ModelSerializer):
    # For GET → show small info
    student = StudentSerializer(read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    # For POST
    student_id = serializers.IntegerField(write_only=True, required=False)
    course_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id',
            'student', 'course_title',
            'student_id', 'course_id',
            'enrolled_at'
        ]
        read_only_fields = ['id', 'enrolled_at']

    def create(self, validated_data):
        student_id = validated_data.pop("student_id", None)
        course_id = validated_data.pop("course_id")

        if student_id:
            student = Student.objects.get(id=student_id)
        else:
            # Create or get student from email if provided
            email = self.context.get('request').data.get('email')
            if email:
                student, _ = Student.objects.get_or_create(
                    email=email,
                    defaults={'name': email.split('@')[0]}
                )
            else:
                raise serializers.ValidationError("Student ID or email is required")

        course = Course.objects.get(id=course_id)

        return Enrollment.objects.create(student=student, course=course)


# ---------------- STAFF MESSAGE ----------------
class StaffMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffMessage
        fields = '__all__'


# ---------------- ASSIGNMENT ----------------
class AssignmentSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.username", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Assignment
        fields = "__all__"


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.username", read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = "__all__"

# ---------------- ATTENDANCE ----------------
class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)
    student_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'month', 'percentage', 'student_id', 'student_name']
        read_only_fields = ['id']

    def create(self, validated_data):
        student_id = validated_data.pop("student_id")
        student = Student.objects.get(id=student_id)
        return Attendance.objects.create(student=student, **validated_data)


# ---------------- COURSE PROGRESS ----------------
class CourseProgressSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    student_name = serializers.CharField(source="student.name", read_only=True)
    
    course_id = serializers.IntegerField(write_only=True)
    student_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CourseProgress
        fields = [
            'id', 'progress', 'course_id', 'student_id',
            'course_title', 'student_name'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        course_id = validated_data.pop("course_id")
        student_id = validated_data.pop("student_id")
        
        course = Course.objects.get(id=course_id)
        student = Student.objects.get(id=student_id)
        
        return CourseProgress.objects.create(
            course=course,
            student=student,
            **validated_data
        )


class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = "__all__"


# ---------------- QUIZ ----------------
class QuizOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizOption
        fields = ['id', 'option_text', 'is_correct', 'order']
        read_only_fields = ['id']


class QuizQuestionSerializer(serializers.ModelSerializer):
    options = QuizOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'question_type', 'points', 'order', 'options']
        read_only_fields = ['id']


class QuizSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.username", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    questions = QuizQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'time_limit', 'passing_score',
            'staff', 'staff_name', 'course', 'course_title',
            'created_at', 'updated_at', 'questions', 'questions_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_questions_count(self, obj):
        return obj.questions.count()


class QuizAttemptSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.username", read_only=True)
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz', 'quiz_title', 'student', 'student_name',
            'score', 'total_questions', 'correct_answers',
            'started_at', 'completed_at', 'is_passed'
        ]
        read_only_fields = ['id', 'started_at', 'score', 'total_questions', 'correct_answers', 'is_passed']


class QuizAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.question_text", read_only=True)
    selected_option_text = serializers.CharField(source="selected_option.option_text", read_only=True)
    
    class Meta:
        model = QuizAnswer
        fields = ['id', 'attempt', 'question', 'question_text', 'selected_option', 'selected_option_text', 'is_correct']
        read_only_fields = ['id', 'is_correct']


# ---------------- LIVE CLASS ----------------
class LiveClassSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.username", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    attendees_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LiveClass
        fields = [
            'id', 'title', 'description', 'meeting_link', 'scheduled_date',
            'duration', 'status', 'staff', 'staff_name', 'course', 'course_title',
            'created_at', 'updated_at', 'attendees_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_attendees_count(self, obj):
        return obj.attendances.count()


class LiveClassAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.username", read_only=True)
    live_class_title = serializers.CharField(source="live_class.title", read_only=True)
    
    class Meta:
        model = LiveClassAttendance
        fields = [
            'id', 'live_class', 'live_class_title', 'student', 'student_name',
            'joined_at', 'left_at', 'duration_minutes'
        ]
        read_only_fields = ['id', 'joined_at']
