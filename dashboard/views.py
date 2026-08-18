from django.shortcuts import render

def admin_overview(request):
    return render(request, 'dashboard/admin_overview.html')