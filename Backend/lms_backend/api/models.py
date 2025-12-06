from django.db import models
from django.contrib.auth.models import User

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration = models.CharField(max_length=50)
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)

class Staff(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=60, blank=True)
    def __str__(self): return self.name

class StaffMessage(models.Model):
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender_name}"

class Student(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    def __str__(self): return self.name

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.student.name} -> {self.course.title}"

class Assignment(models.Model):
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_assignments", null=True,           
        blank=True )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments", null=True, blank=True)
    title = models.CharField(max_length=200, null=True,           # ADD
        blank=True )
    description = models.TextField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    file = models.FileField(upload_to="assignments/", blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assignment_submissions")
    file = models.FileField(upload_to="submissions/")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} → {self.assignment.title}"


class Attendance(models.Model):
    month = models.CharField(max_length=20)
    percentage = models.FloatField(default=0)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    
    def __str__(self):
        return f"{self.student.name} - {self.month} ({self.percentage}%)"


class CourseProgress(models.Model):
    progress = models.IntegerField(default=0)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progress_records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='progress')
    
    def __str__(self):
        return f"{self.student.name} - {self.course.title} ({self.progress}%)"
    

class SiteSetting(models.Model):
    site_name = models.CharField(max_length=150, default="SkillUp LMS")
    admin_email = models.EmailField(blank=True, null=True)
    theme_color = models.CharField(max_length=7, default="#2563eb")
    about = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.site_name


class Quiz(models.Model):
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_quizzes")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes", null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    time_limit = models.IntegerField(default=30, help_text="Time limit in minutes")
    passing_score = models.IntegerField(default=60, help_text="Passing score percentage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=[("multiple_choice", "Multiple Choice"), ("true_false", "True/False")],
        default="multiple_choice"
    )
    points = models.IntegerField(default=1)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order + 1}"


class QuizOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="options")
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.question.quiz.title} - Option {self.order + 1}"


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts")
    score = models.FloatField(default=0)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_passed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} ({self.score}%)"


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuizOption, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.attempt.student.username} - {self.question.quiz.title}"


class LiveClass(models.Model):
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_live_classes")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="live_classes", null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    meeting_link = models.URLField(max_length=500, blank=True, null=True, help_text="Zoom/Google Meet/Other meeting link")
    scheduled_date = models.DateTimeField()
    duration = models.IntegerField(default=60, help_text="Duration in minutes")
    status = models.CharField(
        max_length=20,
        choices=[
            ("scheduled", "Scheduled"),
            ("live", "Live"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled")
        ],
        default="scheduled"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date']

    def __str__(self):
        return f"{self.title} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"


class LiveClassAttendance(models.Model):
    live_class = models.ForeignKey(LiveClass, on_delete=models.CASCADE, related_name="attendances")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="live_class_attendances")
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)

    class Meta:
        unique_together = ['live_class', 'student']

    def __str__(self):
        return f"{self.student.username} - {self.live_class.title}"
