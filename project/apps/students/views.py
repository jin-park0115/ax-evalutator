from django.shortcuts import render


def student_home(request):
    return render(request, "student/home.html")

def student_team(request):
    return render(request, "student/team.html")

def student_result(request):
    return render(request, "student/result.html")