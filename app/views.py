

from django.db import models
from django.utils.timezone import now
from django.core.paginator import Paginator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
import requests
from bs4 import BeautifulSoup
import uuid
from .models import WikiPage, InfoBoxField, InfoBoxValue

# Scraper function
def scrape_wikipedia_pages(urls):
    scraped_data = []
    for url in urls:
        if 'https' not in url:
            continue
        try:
            # import pdb ; pdb.set_trace()
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.find('h1').text if soup.find('h1') else 'No Title'
            info_box = soup.find('table', class_='infobox')
            fields = []

            if info_box:
                rows = info_box.find_all('tr')
                for row in rows:
                    header = row.find('th')
                    data = row.find('td')
                    if header and data:
                        fields.append((header.text.strip(), data.text.strip()))

            scraped_data.append({
                'title': title,
                'url': url,
                'fields': fields,
            })
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    return scraped_data

# Save scraped data
def save_scraped_data(data):
    for entry in data:
        try:
            page, _ = WikiPage.objects.get_or_create(title=entry['title'], url=entry['url'])
            for field_name, field_value in entry['fields']:
                field, _ = InfoBoxField.objects.get_or_create(name=field_name)
                InfoBoxValue.objects.create(value=field_value, field=field, page=page)
        except Exception as e:
            print(f"Error saving data for {entry['title']}: {e}")

# API View for Scraping
class ScrapeWikipediaView(APIView):
    def post(self, request):
        try:
            # import pdb ; pdb.set_trace()
            urls = request.data.get('urls', [])
            if len(urls) > 50:
                return Response({'error': 'Cannot process more than 50 URLs at a time.'}, status=400)

            scraped_data = scrape_wikipedia_pages(urls)
            save_scraped_data(scraped_data)

            return Response({'message': 'Scraping completed successfully.'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

# API View for Filters
class FilterView(APIView):
    def get(self, request):
        try:
            field_name = request.query_params.get('field')
            if field_name:
                field = InfoBoxField.objects.filter(name=field_name).first()
                if field:
                    values = InfoBoxValue.objects.filter(field=field).values_list('value', flat=True).distinct()
                    paginator = Paginator(values, 10)
                    page_number = request.query_params.get('page', 1)
                    return Response({'values': paginator.get_page(page_number).object_list})
                return Response({'error': 'Field not found'}, status=404)

            fields = InfoBoxField.objects.values_list('name', flat=True).distinct()
            paginator = Paginator(fields, 10)
            page_number = request.query_params.get('page', 1)
            return Response({'fields': paginator.get_page(page_number).object_list})
        except Exception as e:
            return Response({'error': str(e)}, status=500)



class FilteredResultsView(APIView):
    def get(self, request):
        try:
            # Extract filters from query parameters
            filters = []
            index = 0
            while True:
                field_key = f'filters[{index}][field]'
                value_key = f'filters[{index}][value]'
                
                # Check if both field and value exist in the query parameters
                if field_key in request.query_params and value_key in request.query_params:
                    filters.append({
                        'field': request.query_params[field_key],
                        'value': request.query_params[value_key],
                    })
                    index += 1
                else:
                    break

            # Ensure filters are provided
            if not filters:
                return Response({'error': 'No filters provided'}, status=400)
            
            # Start with all WikiPages
            pages = WikiPage.objects.all()

            # Apply each filter
            for filter_item in filters:
                field_name = filter_item['field']
                field_value = filter_item['value']
                
                # Check if the field exists
                field = InfoBoxField.objects.filter(name=field_name).first()
                if field:
                    pages = pages.filter(infoboxvalue__field=field, infoboxvalue__value=field_value)
                else:
                    return Response({'error': f'Field "{field_name}" not found'}, status=404)

            # Ensure distinct pages
            distinct_pages = pages.distinct()

            # Paginate results
            paginator = Paginator(distinct_pages, 10)
            page_number = request.query_params.get('page', 1)
            paginated_pages = paginator.get_page(page_number)

            # Return filtered and paginated results
            return Response({
                'pages': [
                    {'title': page.title, 'url': page.url, 'timestamp': page.timestamp} 
                    for page in paginated_pages.object_list
                ],
                'total_pages': paginator.num_pages,
                'current_page': page_number,
            })

        except Exception as e:
            return Response({'error': str(e)}, status=500)

# Additional API View for Fetching All InfoBox Values for a Field
class AllValuesForFieldView(APIView):
    def get(self, request):
        try:
            field_name = request.query_params.get('field')
            if not field_name:
                return Response({'error': 'Field parameter is required'}, status=400)

            field = InfoBoxField.objects.filter(name=field_name).first()
            if not field:
                return Response({'error': 'Field not found'}, status=404)

            values = InfoBoxValue.objects.filter(field=field).values_list('value', flat=True).distinct()
            return Response({'values': list(values)})
        except Exception as e:
            return Response({'error': str(e)}, status=500)
