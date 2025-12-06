from django.contrib import admin
from .models import ContactMessage,Course,Category,Student,Staff,Enrollment
from .models import StaffMessage

admin.site.register([ContactMessage, Staff, Student, Enrollment,StaffMessage])

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'duration')
    list_filter = ('category',)