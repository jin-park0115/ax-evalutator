from django.shortcuts import render


def student_home(request):
    return render(request, "student/home.html")