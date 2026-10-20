from django.http import HttpResponse


def placeholder_view(request):
    return HttpResponse("Accounts placeholder")
