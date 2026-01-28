from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from providers.models import Provider, Service, Certification
from users.models import User


class ProviderRequiredMixin(LoginRequiredMixin):
    """Mixin to require provider user type."""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is authenticated and is a provider."""
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.user_type != 'provider':
            messages.error(request, 'This page is only available to providers.')
            return redirect('login')
        
        return super().dispatch(request, *args, **kwargs)


class ProviderDashboardView(ProviderRequiredMixin, TemplateView):
    """Provider dashboard view."""
    
    template_name = 'providers/dashboard.html'
    
    def get_context_data(self, **kwargs):
        """Add provider data to context."""
        context = super().get_context_data(**kwargs)
        
        try:
            provider = Provider.objects.get(user=self.request.user)
            context['provider'] = provider
            # Use direct query for related objects
            context['services'] = Service.objects.filter(provider=provider, is_active=True)
            context['certifications'] = Certification.objects.filter(provider=provider)
            
            # Calculate stats
            from reviews.models import Review
            reviews = Review.objects.filter(provider=provider)
            if reviews.exists():
                context['total_reviews'] = reviews.count()
                context['average_rating'] = sum(r.rating for r in reviews) / reviews.count()
            else:
                context['total_reviews'] = 0
                context['average_rating'] = 0
        except Provider.DoesNotExist:
            # Provider profile not yet created, redirect to create
            context['provider'] = None
            context['message'] = 'Please complete your profile to get started.'
        
        return context
