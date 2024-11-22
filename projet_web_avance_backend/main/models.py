from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
from django.utils import timezone


# Ce fichier contient nos modèles.
# Un modèle est équivalent à une table de la base de
# données
class CustomUser(AbstractUser):
    user_type = models.CharField(max_length=20, choices=[
        ('administrateur', 'Administrateur'),
        ('gerant', 'Gérant'),
        ('client', 'Client')
    ])
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15, unique=False, blank=True, null=True, default="0000000000")
    email = models.EmailField(max_length=255, unique=False, blank=True, null=True, default="default@gmail.com")

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # Définir un related_name unique
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # Définir un related_name unique
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Commande(models.Model):
    date_commande = models.DateTimeField("date de commande", auto_now_add=True)
    cout_total = models.IntegerField("cout total de la commande", blank=False,
                                     null=False,
                                     help_text="Coût de la commande")
    statut = models.CharField(max_length=50)
    client = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name="Client de la commande",
                               on_delete=models.CASCADE, related_name="client")


class TypeProduit(models.Model):
    '''
        La classe TypeProduit represente le type du produit
            - Exemple: Parfum, Crème, ...
    '''
    intitule = models.CharField("Intitulé du type de produit", max_length=50,
                                unique=True)


class CategorieProduit(models.Model):
    '''
        La classe CategorieProduit represente la catégorie du produit
            - Exemple: Homme, Femme, ...
    '''
    intitule = models.CharField("Intitulé de la catégorie de produit",
                                max_length=50, unique=True)


class Produit(models.Model):
    nom = models.CharField("Nom du produit", max_length=50)
    quantite = models.IntegerField("Quantité en stock")
    cout_unitaire = models.IntegerField("Prix unitaire de vente du produit")
    description = models.TextField("Description du produit")
    type_produit = models.ForeignKey(TypeProduit, on_delete=models.CASCADE)
    categorie_produit = models.ForeignKey(CategorieProduit,
                                          on_delete=models.CASCADE)

class Reapprovisionnement(models.Model):
    date_reapprovisionnement = models.DateField("Date de réapprovisionnement",
                                                auto_now=False,
                                                auto_now_add=False,
                                                default=timezone.now)
    fournisseur = models.CharField("Nom du fournisseur", max_length=50)
    prix_unitaire = models.IntegerField("Prix unitaire du produit")
    quantite = models.IntegerField("Quantité reçue")
    prix_total = models.IntegerField(editable=False)  # Calculé automatiquement
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Calculer le coût total
        self.prix_total = self.prix_unitaire * self.quantite

        # Vérifier que le produit est bien défini avant de tenter d'y accéder
        if self.produit:
            # Augmenter la quantité du produit concerné
            self.produit.quantite += self.quantite
            self.produit.save()
        else:
            raise ValueError("Aucun produit associé à ce réapprovisionnement.")

        # Si la date de réapprovisionnement n'est pas fournie, prendre la date actuelle
        if not self.date_reapprovisionnement:
            self.date_reapprovisionnement = timezone.now().date()

        super(Reapprovisionnement, self).save(*args, **kwargs)


class ProduitCommande(models.Model):
    '''
        La classe ProduitCommande (Produit commandé) contient les infos
        d'un produit commandé
    '''
    quantite = models.IntegerField()
    cout_total = models.IntegerField()
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
