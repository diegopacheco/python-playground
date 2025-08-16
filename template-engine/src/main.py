import re

class TemplateEngine:
    def __init__(self, context=None):
        self.context = context or {}
    
    def render(self, template):
        def replace_var(match):
            var_name = match.group(1)
            if '.' in var_name:
                parts = var_name.split('.')
                value = self.context
                for part in parts:
                    value = value.get(part, '')
                return str(value)
            return str(self.context.get(var_name, ''))
        return re.sub(r'\{\{(\w+(?:\.\w+)*)\}\}', replace_var, template)
    
    def update_context(self, **kwargs):
        self.context.update(kwargs)

engine = TemplateEngine({
    'user': {'name': 'Alice', 'age': 30},
    'app': {'name': 'MyApp', 'version': '1.0'}
})

template = "Welcome {{user.name}} to {{app.name}} v{{app.version}}!"
result = engine.render(template)
print(result)