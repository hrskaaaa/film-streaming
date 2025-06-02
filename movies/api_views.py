from rest_framework import generics
from .models import Content
from .serializers import ContentSerializer
from datetime import date
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # кількість новинок на сторінку

class RecentContentAPIView(ListAPIView):
    serializer_class = ContentSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Content.objects.filter(release_date__isnull=False).order_by('-release_date')

class PopularContentAPIView(generics.ListAPIView):
    serializer_class = ContentSerializer

    def get_queryset(self):
        return Content.objects.filter(rating__isnull=False).order_by('-rating')[:25]
