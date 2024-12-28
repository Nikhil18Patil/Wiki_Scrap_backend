
from django.urls import path
from .views import ScrapeWikipediaView, FilterView, FilteredResultsView, AllValuesForFieldView

urlpatterns = [
    path('api/scrape/', ScrapeWikipediaView.as_view(), name='scrape_wikipedia'),
    path('api/filters/', FilterView.as_view(), name='filters'),
    path('api/filtered-results/', FilteredResultsView.as_view(), name='filtered_results'),
    path('api/all-values/', AllValuesForFieldView.as_view(), name='all_values_for_field'),
]