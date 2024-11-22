from django.contrib import admin
from .models import CustomUser  # Assure-toi d'importer ton modèle personnalisé

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'phone_number', )

admin.site.register(CustomUser, CustomUserAdmin)
