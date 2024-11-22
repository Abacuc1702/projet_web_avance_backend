from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Commande, TypeProduit, CategorieProduit, \
        Produit, Reapprovisionnement, ProduitCommande


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 
                  'phone_number', 'user_type', 'email']

    def create(self, validated_data):
        # Utiliser la méthode create_user pour que le mot de passe soit haché 
        # correctement
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data['phone_number'],
            user_type=validated_data['user_type'],
            email=validated_data['email']
        )
        return user


class CommandeSerializer(serializers.ModelSerializer):
    client = CustomUserSerializer(read_only=True)
    # gerant = CustomUserSerializer(read_only=True)

    class Meta:
        model = Commande
        fields = ['id', 'date_commande', 'cout_total', 'statut', 'client']


class TypeProduitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeProduit
        fields = ['id', 'intitule']


class CategorieProduitSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieProduit
        fields = ['id', 'intitule']


class ProduitSerializer(serializers.ModelSerializer):
    type_produit = TypeProduitSerializer(read_only=True)
    categorie_produit = CategorieProduitSerializer(read_only=True)
    type_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=TypeProduit.objects.all(), source='type_produit', write_only=True)
    categorie_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=CategorieProduit.objects.all(), source='categorie_produit', write_only=True)

    class Meta:
        model = Produit
        fields = ['id', 'nom', 'quantite', 'cout_unitaire', 'description',
                  'type_produit', 'categorie_produit', 'type_produit_id', 'categorie_produit_id']

        
    def create(self, validated_data):
        return Produit.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.nom = validated_data.get('nom', instance.nom)
        instance.quantite = validated_data.get('quantite', instance.quantite)
        instance.cout_unitaire = validated_data.get('cout_unitaire', instance.cout_unitaire)
        instance.description = validated_data.get('description', instance.description)
        instance.type_produit = validated_data.get('type_produit', instance.type_produit)
        instance.categorie_produit = validated_data.get('categorie_produit', instance.categorie_produit)
        instance.save()
        return instance
class ReapprovisionnementSerializer(serializers.ModelSerializer):
    produit_id = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all(), source='produit')

    class Meta:
        model = Reapprovisionnement
        fields = ['id', 'date_reapprovisionnement', 'fournisseur', 
                  'prix_unitaire', 'quantite', 'prix_total', 'produit_id']

    def create(self, validated_data):
        # Créer un réapprovisionnement en utilisant les données validées
        produit = validated_data.pop('produit')
        reapprovisionnement = Reapprovisionnement.objects.create(produit=produit, **validated_data)
        return reapprovisionnement


class ProduitCommandeSerializer(serializers.ModelSerializer):
    commande = CommandeSerializer(read_only=True)
    produit = ProduitSerializer(read_only=True)

    class Meta:
        model = ProduitCommande
        fields = ['id', 'quantite', 'cout_total', 'commande', 'produit']
        

class ProduitCommandeCreateSerializer(serializers.ModelSerializer):
    produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(), source='produit')

    class Meta:
        model = ProduitCommande
        fields = ['produit_id', 'quantite', 'cout_total']

class CommandeCreateSerializer(serializers.ModelSerializer):
    produits = ProduitCommandeCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Commande
        fields = ['date_commande', 'cout_total', 'statut', 'produits']

    def create(self, validated_data):
        # print(request)
        produits_data = validated_data.pop('produits')
        commande = Commande.objects.create(**validated_data)
        print(produits_data)

        for produit_data in produits_data:
            prod = produit_data['produit']
            if ProduitCommande.objects.create(
                commande=commande,
                produit=prod,
                quantite=produit_data['quantite'],
                cout_total=prod.cout_unitaire * int(produit_data['quantite'])
            ):
                prod.quantite -= produit_data['quantite']
                prod.save()

        return commande