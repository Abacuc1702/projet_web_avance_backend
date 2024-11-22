import datetime
import random
import os
from django.conf import settings
from django.shortcuts import render
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.http import JsonResponse, Http404, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from django.urls import reverse
from rest_framework.response import Response
from rest_framework import generics, status, viewsets, permissions
import urllib.parse
# , viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from .models import CustomUser, TypeProduit, CategorieProduit, Produit, Commande, ProduitCommande, Reapprovisionnement
# , Product
from .serializers import CustomUserSerializer, CategorieProduitSerializer, \
                        TypeProduitSerializer, ProduitSerializer, CommandeCreateSerializer,\
                        ProduitCommandeSerializer, ProduitCommandeCreateSerializer, CommandeSerializer, ReapprovisionnementSerializer

# , ProductSerializer
from .permissions import IsAdminOrSelf, IsAdminOrGerant
# IsAdminOrGerant, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404


class UserCreateView(generics.CreateAPIView):
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        # Autoriser les requêtes non authentifiées par défaut
        if self.request.data.get('user_type') == 'Client':
            return [AllowAny()]
        else:
            return [IsAuthenticated()]

    def perform_create(self, serializer):
        user_type = serializer.validated_data.get('user_type')

        # Pour un utilisateur non-authentifié (client)
        if user_type == 'client':
            serializer.save()

        # Pour un utilisateur authentifié
        elif self.request.user.is_authenticated:
            if self.request.user.user_type != 'administrateur':
                raise PermissionDenied("Only admins can create managers.")
            if user_type == 'administrateur':
                raise PermissionDenied("Admins cannot be created by this\
                    endpoint.")
            serializer.save()

        # Si l'utilisateur n'est pas authentifié et tente de créer un autre
        # type d'utilisateur
        else:
            raise PermissionDenied("Authentication is required to create this\
                type of user.")

class UserList(generics.ListAPIView):
    serializer_class = CustomUserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.user_type == 'administrateur':
                # Administrateurs peuvent voir tous les utilisateurs
                return CustomUser.objects.all()
            elif user.user_type == 'gerant':
                # Gérants peuvent voir seulement les clients
                return CustomUser.objects.filter(user_type='client')
            elif user.user_type == 'client':
                # Les clients ne peuvent rien voir
                return CustomUser.objects.none()
        else:
            raise PermissionDenied("Authentication is required to view this list.")

class UserUpdateDeleteView(viewsets.GenericViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAdminOrSelf]

    @action(detail=True, methods=['put', 'patch'])
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        self.check_object_permissions(request, user)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(CustomUserSerializer(self.perform_update(serializer)).data)


    def perform_update(self, serializer):
        if self.request.user.is_authenticated:
            obj = self.get_object() 
            # if self.request.user.user_type == 'administrateur' and obj != self.request.user:
            #     raise PermissionDenied("Admins cannot modify other admin's information.")
            user = serializer.save()
            if 'password' in serializer.validated_data:
                password = serializer.validated_data['password']
                user.set_password(password)  # Hash the password
                user.save()
            return user
        else:
            raise PermissionDenied("Authentication is required to modify this user's information.")

    @action(detail=True, methods=['delete'])
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        self.check_object_permissions(request, user)
        return self.perform_destroy(user)

    def perform_destroy(self, instance):
        # Seul un administrateur peut désactiver un gérant
        if instance.user_type == 'gerant' and self.request.user.user_type != 'administrateur':
            raise PermissionDenied("Only an administrator can deactivate a manager's account.")
        
        # Désactiver le compte plutôt que de le supprimer
        # instance.is_active = False
        instance.delete()

        return Response({"detail": "User account has been deactivated."}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def activate_user(self, request, *args, **kwargs):
        # Seul un administrateur peut activer un compte
        if request.user.user_type != 'administrateur':
            raise PermissionDenied("Only an administrator can activate a user's account.")

        user = get_object_or_404(CustomUser, pk=kwargs['pk'])

        if user.is_active:
            return Response({"detail": "User account is already active."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()

        return Response({"detail": "User account has been activated."}, status=status.HTTP_200_OK)
    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key,
                             'user': CustomUserSerializer(user).data
                             })
        return Response({'error': 'Invalid credentials'},
                        status=status.HTTP_400_BAD_REQUEST)


class TypeProduitViewSet(viewsets.ModelViewSet):
    queryset = TypeProduit.objects.all()
    serializer_class = TypeProduitSerializer
    permission_classes = [IsAdminOrGerant]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAdminOrGerant()]


class CategorieProduitViewSet(viewsets.ModelViewSet):
    queryset = CategorieProduit.objects.all()
    serializer_class = CategorieProduitSerializer
    permission_classes = [IsAdminOrGerant]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAdminOrGerant()]


class ProduitViewSet(viewsets.ModelViewSet):
    queryset = Produit.objects.all()
    serializer_class = ProduitSerializer
    permission_classes = [IsAdminOrGerant]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsAdminOrGerant()]
    
class CommandeCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommandeCreateSerializer
    
    def post(self, request):
        # date_commande = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S")
        statut = "Accepté"
        cout_total = 0
        produits = request.data["produits"]
        errors = {}
        for produit in produits:
            try:
                prod = Produit.objects.get(id=produit["produit_id"])
                if (int(produit["quantite"]) <= 0):
                    errors[prod.nom] = "Veuillez entrer une quantité supérieure à 0"
                else:
                    if (prod.quantite < int(produit["quantite"])) and (prod.quantite  <= 0) :
                        errors[prod.nom] = f"Le produit {prod.nom} n'a plus assez de stock."
                cout_total += prod.cout_unitaire * int(produit["quantite"])
            except Produit.DoesNotExist:
                errors[produit["produit_id"]] = f"Le produit avec pour id '{produit['produit_id']}' n'existe pas."
        if len(errors.keys()) > 0:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user.user_type == 'client':
            user = request.user
        else:
            user = CustomUser.objects.get(id=request.data["user"])
        print(type(user))
        serializer = CommandeCreateSerializer(data={"date_commande": None,
                                                   "statut": statut,
                                                   "cout_total": cout_total,
                                                   "produits":produits})
        if serializer.is_valid():
            serializer.save(client=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        data = []
        if request.user.user_type == 'client':
            queryset = Commande.objects.filter(client=request.user)
        else:
            queryset = Commande.objects.all()
        for command in queryset:
            prod_comm = ProduitCommande.objects.filter(commande=command)
            serializer = CommandeSerializer(command).data
            serializer["produits commandes"] = []
            for pc in prod_comm:
                # print()
                serializer["produits commandes"].append(ProduitCommandeSerializer(pc).data)
            data.append(serializer)
        return Response(data, status=status.HTTP_200_OK)


class ReapprovisionnementListCreateView(generics.ListCreateAPIView):
    queryset = Reapprovisionnement.objects.all()
    serializer_class = ReapprovisionnementSerializer
    # authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrGerant]

class ReapprovisionnementRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Reapprovisionnement.objects.all()
    serializer_class = ReapprovisionnementSerializer
    # authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrGerant]
    
    

class GenererRapport(APIView):
    permission_classes = [IsAdminOrGerant] 
    
    def generate_data(self, start_date="", end_date=""):
        if (start_date == ""):
            start_date = datetime.now().date() - timedelta(days=30)
        if (end_date == ""):
            end_date = datetime.now().date()
        produits = Produit.objects.all()
        # products = [
        #     {"nom": f"Produit {i}", "categorie": random.choice(["Homme", "Femme", "Unisexe"]),
        #     "type": random.choice(["Parfum", "Crème", "Lotion"]),
        #     "quantite": random.randint(10, 100), "cout_unitaire": random.randint(20, 200)}
        #     for i in range(1, 11)
        # ]
        reapprovisionnements = Reapprovisionnement.objects.all()
        # reapprovisionnements = [
        #     {"date": start_date + timedelta(days=random.randint(0, 30)),
        #     "produit": random.choice([p["nom"] for p in products]),
        #     "fournisseur": f"Fournisseur {random.randint(1, 5)}",
        #     "quantite": random.randint(50, 200),
        #     "prix_unitaire": random.randint(10, 100)}
        #     for _ in range(15)
        # ]
        # for r in reapprovisionnements:
        #     r["prix_total"] = r["quantite"] * r["prix_unitaire"]
        
        commandes = Commande.objects.all()
        orders = []
        
        for commande in commandes:
            order = {}
            produits_commandes = ProduitCommande.objects.filter(commande=commande)
            quantite = 0
            for pc in produits_commandes:
                quantite += pc.quantite
            order['date_commande'] = commande.date_commande
            order['client'] = commande.client.first_name+" "+commande.client.last_name
            order['produits_commandes'] = quantite
            order['cout_total'] = commande.cout_total
            order['statut'] = commande.statut
            orders.append(order)
        commandes = orders
        # commandes = [
        #     {"date": start_date + timedelta(days=random.randint(0, 30)),
        #     "client": f"Client {random.randint(1, 20)}",
        #     "produits_commandes": random.randint(1, 5),
        #     "quantite": random.randint(1, 10),
        #     "cout_total": random.randint(50, 500),
        #     "statut": random.choice(["En cours", "Livrée", "Annulée"])}
        #     for _ in range(20)
        # ]
        
        categories = CategorieProduit.objects.all()
        types = TypeProduit.objects.all()
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "produits": produits,
            "reapprovisionnements": reapprovisionnements,
            "commandes": commandes,
            "categories": categories,
            "types": types
        }

    
    def generate_pdf_report(self, data, output_filename):
        doc = SimpleDocTemplate(output_filename, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Titre et introduction
        elements.append(Paragraph("Rapport d'Inventaire et Bilan de Gestion", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Du {data['start_date']} au {data['end_date']}", styles['Normal']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("En tant que gérant de la boutique, je vous présente ce rapport qui dresse un état des lieux de la gestion des stocks, des réapprovisionnements et des commandes effectuées au cours de la période récente.", styles['Normal']))
        elements.append(Spacer(1, 24))

        # 1. Inventaire des Produits
        elements.append(Paragraph("1. Inventaire des Produits", styles['Heading2']))
        produit_data = [["Nom du produit", "Catégorie", "Type", "Quantité en Stock", "Prix Unitaire"]]
        produit_data.extend([[p.nom, p.categorie_produit, p.type_produit.intitule, p.quantite, p.cout_unitaire] for p in data['produits']])
        produit_table = Table(produit_data)
        produit_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1, 0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        elements.append(produit_table)
        elements.append(Spacer(1, 24))

        # 2. Gestion des Réapprovisionnements
        elements.append(Paragraph("2. Gestion des Réapprovisionnements", styles['Heading2']))
        reappro_data = [["Date de réapprovisionnement", "Nom du produit", "Fournisseur", "Quantité reçue", "Prix Unitaire", "Coût total"]]
        reappro_data.extend([[r.date_reapprovisionnement, r.produit.nom, r.fournisseur, r.quantite, r.prix_unitaire, r.prix_total] for r in data['reapprovisionnements']])
        reappro_table = Table(reappro_data)
        reappro_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        elements.append(reappro_table)
        elements.append(Spacer(1, 24))

        # 3. Bilan des Commandes
        elements.append(Paragraph("3. Bilan des Commandes", styles['Heading2']))
        commande_data = [["Date de Commande", "Client", "Produits commandés", "Coût total", "Statut"]]
        commande_data.extend([[c['date_commande'], c['client'], c['produits_commandes'], c['cout_total'], c['statut']] for c in data['commandes']])
        commande_table = Table(commande_data)
        commande_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        elements.append(commande_table)
        elements.append(Spacer(1, 24))

        # 4. Catégories de Produits
        elements.append(Paragraph("4. Catégories de Produits", styles['Heading2']))
        categorie_data = [["Nom de la Catégorie"]]
        categorie_data.extend([[c.intitule] for c in data['categories']])
        categorie_table = Table(categorie_data)
        categorie_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        elements.append(categorie_table)
        elements.append(Spacer(1, 24))

        # 5. Types de Produits
        elements.append(Paragraph("5. Types de Produits", styles['Heading2']))
        type_data = [["Nom du Type"]]
        type_data.extend([[t.intitule] for t in data['types']])
        type_table = Table(type_data)
        type_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        elements.append(type_table)
        elements.append(Spacer(1, 24))

        # Conclusion
        elements.append(Paragraph("Conclusion", styles['Heading2']))
        elements.append(Paragraph("En résumé, la gestion des stocks et des réapprovisionnements est bien maîtrisée. Les commandes sont traitées efficacement, et le suivi des catégories et types de produits est à jour.", styles['Normal']))

        # Génération du PDF
        doc.build(elements)
    
        
    def post(self, request):
        start_date =  request.data['startDate']
        end_date = request.data['endDate']
        
        data = self.generate_data(start_date, end_date)
        self.generate_pdf_report(data=data, output_filename=f'rapports/Rapport_du_{start_date}_au_{end_date}.pdf')
        
        return Response({
            "message": "created successfully"
        })


@api_view(['GET'])
@permission_classes([IsAdminOrGerant])
def list_pdfs(request):
    # Dossier où sont stockés les fichiers PDF
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'rapports')

    # Vérifier que le répertoire existe
    if not os.path.exists(pdf_dir):
        return Response({"detail": "Le dossier n'existe pas."}, status=404)

    # Lister tous les fichiers PDF dans le dossier
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

    # Construire les URLs de téléchargement pour chaque fichier
    pdf_urls = [
        {
            "filename": pdf,
            "url": request.build_absolute_uri(reverse('download', args=[urllib.parse.quote(pdf)]))
        } 
        for pdf in pdf_files
    ]

    # Retourner la liste des fichiers avec leurs URLs de téléchargement
    return Response(pdf_urls)


@api_view(['GET'])
@permission_classes([IsAdminOrGerant])
def download_pdf(request, filename):
    # Chemin absolu vers le fichier PDF
    file_path = os.path.join(settings.MEDIA_ROOT, 'rapports', filename)

    # Vérifier si le fichier existe
    if os.path.exists(file_path):
        with open(file_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    else:
        return Response({"detail": "Le fichier n'existe pas."}, status=404)
