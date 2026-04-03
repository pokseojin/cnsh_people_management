from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def cnsh_map(request):
    return render(request, 'cnsh_map.html', {})