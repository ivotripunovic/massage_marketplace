from django.conf import settings


def subscription_price(request):
    return {"subscription_price": settings.SUBSCRIPTION_AMOUNT}
