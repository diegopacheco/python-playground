from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import json
import os
from datetime import datetime
from app.models import Record

@csrf_exempt
def save(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        number = data.get('number')
        date_str = data.get('date')
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        record = Record.objects.create(number=number, date=date_obj)
        return JsonResponse({'id': record.id, 'number': record.number, 'date': str(record.date)})
    return JsonResponse({'error': 'Invalid method'}, status=400)

def read(request):
    if request.method == 'GET':
        records = Record.objects.all()
        data = [{'id': r.id, 'number': r.number, 'date': str(r.date)} for r in records]
        return JsonResponse({'records': data})
    return JsonResponse({'error': 'Invalid method'}, status=400)

def getlast(request):
    if request.method == 'GET':
        return HttpResponseRedirect('http://localhost:8001/getlast')
    return JsonResponse({'error': 'Invalid method'}, status=400)
