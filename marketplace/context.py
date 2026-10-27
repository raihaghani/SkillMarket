from .services import has_role
def roles(request):
    return {'is_seller': has_role(request.user, 'Seller'), 'is_buyer': has_role(request.user, 'Buyer')}
