from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Reapprovisionnement
from django.conf import settings


@receiver(post_save, sender=Reapprovisionnement)
def send_reapprovisionnement_mail(sender, instance, created, **kwargs):
    if created:
        sujet = "Nouveau réapprovisionnement"
        message = f"Un nouveau réapprovisionnement a été créé pour le produit {instance.produit.nom}."
        recipient_list = ['abacucagbedje@gmail.com']
        send_mail(sujet, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
