import json
import time
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class CheckerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'checker'
    
    ids_dict = {}
    def ready(self):
        start_time = time.time()
        try:
            with open('config/ids.json', 'r') as f:
                ids_list = json.load(f)
                self.ids_dict = {id_val: True for id_val in ids_list}
        except FileNotFoundError:
            logger.error("config/ids.json not found")
            self.ids_dict = {}
        
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000
        
        print(f"Loaded {len(self.ids_dict)} IDs into memory in {load_time_ms:.2f} milliseconds")