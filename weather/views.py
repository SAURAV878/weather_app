from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def test(request):
    return Response({
        'message': 'Weather Api working'
    })

# Create your views here.
