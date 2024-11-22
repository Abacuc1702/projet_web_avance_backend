"""
    Ce fichier, comme son nom l'indique,
    nous permet de créer les différentes
    permissions des utilisateurs
"""

from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
        les permissions de l'administrateur
    """
    def has_permission(self, request, view):
        return request.user and request.user.user_type == 'administrateur'


class IsAdminOrGerant(BasePermission):
    """
        Les permissions de l'admin et du gérant
    """
    def has_permission(self, request, view):
        try:
            if view.action == 'list':
                return True
            else:
                if request.user.is_authenticated:
                    return request.user and (
                        request.user.user_type == 'administrateur' or
                        request.user.user_type == 'gerant')
                else:
                    False
        except:
            if request.method == 'GET':
                return True
            else:
                if request.user.is_authenticated:
                    return request.user and (
                        request.user.user_type == 'administrateur' or
                        request.user.user_type == 'gerant')
                else:
                    return False


class IsAdminOrSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            return request.user == obj or \
                request.user.user_type == 'administrateur'
        else:
            return False
