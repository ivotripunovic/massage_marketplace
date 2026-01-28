from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.db.models import Q
from payments.models import SubscriptionPayment
from providers.models import Provider


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin to require admin user type."""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is authenticated and is an admin."""
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.user_type != 'admin':
            return HttpResponseForbidden('You do not have permission to access this page.')
        
        return super().dispatch(request, *args, **kwargs)


class AdminPaymentListView(AdminRequiredMixin, ListView):
    """View for listing all subscription payments (admin only)."""
    
    model = SubscriptionPayment
    template_name = 'admin/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 50
    
    def get_queryset(self):
        """Get all payments with related provider info."""
        queryset = SubscriptionPayment.objects.select_related(
            'provider__user'
        ).order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status', '').strip()
        if status and status in ['pending', 'completed', 'failed']:
            queryset = queryset.filter(status=status)
        
        # Filter by payment method
        method = self.request.GET.get('method', '').strip()
        if method:
            queryset = queryset.filter(payment_method=method)
        
        # Search by provider email or reference ID
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(provider__user__email__icontains=search) |
                Q(reference_id__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add filter values and payment methods to context."""
        context = super().get_context_data(**kwargs)
        
        context['status'] = self.request.GET.get('status', '')
        context['method'] = self.request.GET.get('method', '')
        context['search'] = self.request.GET.get('search', '')
        
        context['status_choices'] = ['pending', 'completed', 'failed']
        context['method_choices'] = [
            ('crypto_bitcoin', 'Bitcoin'),
            ('crypto_ethereum', 'Ethereum'),
            ('crypto_usdc', 'USDC'),
            ('bank_transfer', 'Bank Transfer'),
        ]
        
        return context


class AdminPaymentDetailView(AdminRequiredMixin, DetailView):
    """View for viewing payment details (admin only)."""
    
    model = SubscriptionPayment
    template_name = 'admin/payment_detail.html'
    context_object_name = 'payment'
    pk_url_kwarg = 'pk'
    
    def get_queryset(self):
        """Get payment with related provider info."""
        return SubscriptionPayment.objects.select_related('provider__user')
