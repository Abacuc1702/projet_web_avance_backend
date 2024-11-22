from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserCreateView, UserUpdateDeleteView, LoginView, \
    TypeProduitViewSet, CategorieProduitViewSet, ProduitViewSet, CommandeCreateView, UserList, ReapprovisionnementRetrieveUpdateDestroyView, ReapprovisionnementListCreateView, GenererRapport, download_pdf, list_pdfs
# , ProductViewSet

router = DefaultRouter()
router.register(r'type-produit', TypeProduitViewSet)
router.register(r'categorie-produit', CategorieProduitViewSet)
router.register(r'produit', ProduitViewSet)


user_update_delete = UserUpdateDeleteView.as_view({
    'post': 'activate_user',
    'delete': 'delete_user',
})


urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserCreateView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user/<int:pk>/update/', UserUpdateDeleteView.as_view({'put': 'update', 'patch': 'update'}), name='user-update'),
    path('user/<int:pk>/delete/', UserUpdateDeleteView.as_view({'delete': 'destroy'}), name='user-delete'),
    path('user/<int:pk>/activate/', UserUpdateDeleteView.as_view({'post': 'activate_user'}), name='user-activate'),
    path('users', UserList.as_view(), name='user-list'),
    path('commandes/', CommandeCreateView.as_view(), name='create-commande'),
    path('reapprovisionnements/', ReapprovisionnementListCreateView.as_view(), name='reapprovisionnement-list-create'),
    path('reapprovisionnements/<int:pk>/', ReapprovisionnementRetrieveUpdateDestroyView.as_view(), name='reapprovisionnement-detail'),
    path('rapports/', GenererRapport.as_view(), name='rapports'),
    path('rapports/list', list_pdfs, name='liste_rapports'),
    path('download/<str:filename>/', download_pdf, name='download')
]
