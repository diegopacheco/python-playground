import time
from django.http import JsonResponse
from django.apps import apps

def check_id(request, id):
    start_time = time.time()
    
    checker_config = apps.get_app_config('checker')
    id_str = str(id)
    
    if id_str in checker_config.ids_dict:
        result = "good to go"
    else:
        result = "no dounuts for you"
    
    end_time = time.time()
    check_time_ms = (end_time - start_time) * 1000
    print(f"ID check took {check_time_ms:.4f} milliseconds")
    
    return JsonResponse({"message": result})