from django.shortcuts import render


def student_home(request):
    # state = get_student_state(request.user) 
    state = "before"
    return render(request, "student/home.html", {"state": state})

def student_team(request):
    return render(request, "student/team.html")

def student_result(request):
    return render(request, "student/result.html")