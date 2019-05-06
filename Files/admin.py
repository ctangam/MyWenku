from django.contrib import admin
from .models import File, Channel, First_Category, Second_Category, SearchLog

admin.site.register(File)
admin.site.register(Channel)
admin.site.register(First_Category)
admin.site.register(Second_Category)
admin.site.register(SearchLog)
