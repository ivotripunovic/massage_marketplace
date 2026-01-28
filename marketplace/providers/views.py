from django.views.generic import TemplateView, FormView, UpdateView, CreateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django import forms
from django.db.models import Count, Avg
from django.http import HttpResponseForbidden
from providers.models import Provider, Service, Certification
from providers.forms import CertificationForm, ServiceForm, SubscriptionSettingsForm
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


class ProviderProfileForm(forms.ModelForm):
    """Form for updating provider profile."""
    
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
            'placeholder': 'Last Name'
        })
    )
    
    class Meta:
        model = Provider
        fields = ('bio', 'phone', 'photo')
        labels = {
            'bio': 'Bio / About',
            'phone': 'Phone Number',
            'photo': 'Profile Photo',
        }
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
                'placeholder': 'Tell clients about your experience and specialties',
                'rows': 4
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
                'placeholder': '+1 (555) 123-4567',
                'type': 'tel'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700',
                'accept': 'image/jpeg,image/png,image/gif',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with user data."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
    
    def clean_photo(self):
        """Validate photo file."""
        photo = self.cleaned_data.get('photo')
        
        if photo:
            # Check file size (< 5MB)
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Image must be smaller than 5MB')
            
            # Check file format
            valid_formats = ['image/jpeg', 'image/png', 'image/gif']
            if photo.content_type not in valid_formats:
                raise forms.ValidationError('Only JPEG, PNG, and GIF images are allowed')
            
            # Validate that it's a real image
            try:
                from PIL import Image
                img = Image.open(photo)
                img.verify()
                # Reset file pointer after verification
                photo.seek(0)
            except Exception:
                raise forms.ValidationError('The uploaded file is not a valid image')
        
        return photo
    
    def save(self, commit=True):
        """Save form and update user fields."""
        provider = super().save(commit=False)
        
        # Update user first and last name
        user = provider.user
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        
        # Resize image if provided
        if provider.photo:
            self._resize_image(provider)
        
        if commit:
            user.save()
            provider.save()
        
        return provider
    
    def _resize_image(self, provider):
        """Resize image to maximum 800x800 pixels."""
        from PIL import Image
        import io
        
        if not provider.photo:
            return
        
        # Read the image
        img = Image.open(provider.photo)
        original_format = img.format
        
        # Check if resizing is needed
        if img.height > 800 or img.width > 800:
            # Create thumbnail
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Save the resized image back to the field
            img_io = io.BytesIO()
            
            # Determine format from filename or image format
            filename_lower = provider.photo.name.lower()
            if filename_lower.endswith('.png'):
                save_format = 'PNG'
            elif filename_lower.endswith('.gif'):
                save_format = 'GIF'
            else:  # Default to JPEG
                save_format = 'JPEG'
            
            # If original image had a format, use that
            if original_format:
                save_format = original_format
            
            img.save(img_io, format=save_format)
            img_io.seek(0)
            provider.photo.save(provider.photo.name, img_io, save=False)


class ProviderProfileUpdateView(ProviderRequiredMixin, FormView):
    """View for updating provider profile."""
    
    template_name = 'providers/profile_edit.html'
    form_class = ProviderProfileForm
    success_url = reverse_lazy('provider_dashboard')
    
    def get_form_kwargs(self):
        """Pass provider instance to form."""
        kwargs = super().get_form_kwargs()
        try:
            provider = Provider.objects.get(user=self.request.user)
            kwargs['instance'] = provider
        except Provider.DoesNotExist:
            # Create new provider if doesn't exist
            provider = Provider.objects.create(user=self.request.user, phone='')
            kwargs['instance'] = provider
        return kwargs
    
    def form_valid(self, form):
        """Handle valid form."""
        form.save()
        messages.success(self.request, 'Your profile has been updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add provider data to context."""
        context = super().get_context_data(**kwargs)
        context['provider'] = Provider.objects.get(user=self.request.user)
        return context


class CertificationCreateView(ProviderRequiredMixin, CreateView):
    """View for adding new certification."""
    
    model = Certification
    form_class = CertificationForm
    template_name = 'providers/certification_form.html'
    success_url = reverse_lazy('provider_profile')
    
    def form_valid(self, form):
        """Handle valid form - assign to current provider."""
        try:
            provider = Provider.objects.get(user=self.request.user)
            form.instance.provider = provider
            messages.success(self.request, 'Certification added successfully.')
        except Provider.DoesNotExist:
            messages.error(self.request, 'Provider profile not found.')
            return redirect('provider_profile')
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add provider to context."""
        context = super().get_context_data(**kwargs)
        context['provider'] = Provider.objects.get(user=self.request.user)
        return context


class CertificationDeleteView(ProviderRequiredMixin, DeleteView):
    """View for deleting certification."""
    
    model = Certification
    success_url = reverse_lazy('provider_profile')
    pk_url_kwarg = 'pk'
    http_method_names = ['post']
    
    def get_object(self, queryset=None):
        """Get certification and verify ownership."""
        cert = super().get_object(queryset)
        
        # Verify the certification belongs to the current provider
        try:
            provider = Provider.objects.get(user=self.request.user)
            if cert.provider != provider:
                messages.error(self.request, 'You do not have permission to delete this certification.')
                redirect_response = redirect('provider_profile')
                redirect_response.status_code = 403
                raise PermissionError('Certification does not belong to this provider')
        except Provider.DoesNotExist:
            messages.error(self.request, 'Provider profile not found.')
            raise PermissionError('Provider profile not found')
        
        return cert
    
    def post(self, request, *args, **kwargs):
        """Handle deletion with message."""
        try:
            messages.success(request, 'Certification deleted successfully.')
            return super().post(request, *args, **kwargs)
        except (PermissionError, Certification.DoesNotExist):
            return redirect('provider_profile')
    
    def get_context_data(self, **kwargs):
        """Add provider to context for certification delete."""
        context = super().get_context_data(**kwargs)
        context['provider'] = Provider.objects.get(user=self.request.user)
        return context


class ServiceListView(ProviderRequiredMixin, ListView):
    """View for listing provider's services."""
    
    model = Service
    template_name = 'providers/service_list.html'
    context_object_name = 'services'
    paginate_by = 20
    
    def get_queryset(self):
        """Get services for current provider."""
        try:
            provider = Provider.objects.get(user=self.request.user)
            return Service.objects.filter(provider=provider).order_by('-created_at')
        except Provider.DoesNotExist:
            return Service.objects.none()
    
    def get_context_data(self, **kwargs):
        """Add provider to context."""
        context = super().get_context_data(**kwargs)
        context['provider'] = Provider.objects.get(user=self.request.user)
        return context


class ServiceCreateView(ProviderRequiredMixin, CreateView):
    """View for creating a new service."""
    
    model = Service
    form_class = ServiceForm
    template_name = 'providers/service_form.html'
    success_url = reverse_lazy('provider_dashboard')
    
    def form_valid(self, form):
        """Handle valid form - assign to current provider."""
        try:
            provider = Provider.objects.get(user=self.request.user)
            form.instance.provider = provider
            messages.success(self.request, 'Service created successfully.')
        except Provider.DoesNotExist:
            messages.error(self.request, 'Provider profile not found.')
            return redirect('provider_dashboard')
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add provider to context."""
        context = super().get_context_data(**kwargs)
        context['provider'] = Provider.objects.get(user=self.request.user)
        context['action'] = 'Create Service'
        return context


class ServiceUpdateView(ProviderRequiredMixin, UpdateView):
    """View for updating a service."""
    
    model = Service
    form_class = ServiceForm
    template_name = 'providers/service_form.html'
    success_url = reverse_lazy('provider_dashboard')
    pk_url_kwarg = 'pk'
    
    def get_object(self, queryset=None):
        """Get service and verify ownership."""
        service = super().get_object(queryset)
        
        # Verify the service belongs to the current provider
        try:
            provider = Provider.objects.get(user=self.request.user)
            if service.provider != provider:
                messages.error(self.request, 'You do not have permission to edit this service.')
                raise PermissionError('Service does not belong to this provider')
        except Provider.DoesNotExist:
            messages.error(self.request, 'Provider profile not found.')
            raise PermissionError('Provider profile not found')
        
        return service
    
    def form_valid(self, form):
        """Handle valid form."""
        try:
            messages.success(self.request, 'Service updated successfully.')
        except Exception:
            pass
        
        return super().form_valid(form)
    
    def post(self, request, *args, **kwargs):
        """Handle POST with error handling."""
        try:
            return super().post(request, *args, **kwargs)
        except (PermissionError, Service.DoesNotExist):
            return redirect('provider_dashboard')
    
    def get_context_data(self, **kwargs):
        """Add provider to context for service update."""
        context = super().get_context_data(**kwargs)
        context['provider'] = Provider.objects.get(user=self.request.user)
        context['action'] = 'Edit Service'
        return context


class ServiceDeleteView(ProviderRequiredMixin, DeleteView):
    """View for deleting a service."""
    
    model = Service
    success_url = reverse_lazy('provider_dashboard')
    pk_url_kwarg = 'pk'
    http_method_names = ['post']
    
    def get_object(self, queryset=None):
        """Get service and verify ownership."""
        service = super().get_object(queryset)
        
        # Verify the service belongs to the current provider
        try:
            provider = Provider.objects.get(user=self.request.user)
            if service.provider != provider:
                messages.error(self.request, 'You do not have permission to delete this service.')
                raise PermissionError('Service does not belong to this provider')
        except Provider.DoesNotExist:
            messages.error(self.request, 'Provider profile not found.')
            raise PermissionError('Provider profile not found')
        
        return service
    
    def post(self, request, *args, **kwargs):
        """Handle deletion with message."""
        try:
            messages.success(request, 'Service deleted successfully.')
            return super().post(request, *args, **kwargs)
        except (PermissionError, Service.DoesNotExist):
            return redirect('provider_dashboard')
    
    def get_context_data(self, **kwargs):
        """Add provider to context for service delete."""
        context = super().get_context_data(**kwargs)
        context['provider'] = Provider.objects.get(user=self.request.user)
        return context


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin to require admin user type."""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is authenticated and is an admin."""
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.user_type != 'admin':
            return HttpResponseForbidden('You do not have permission to access this page.')
        
        return super().dispatch(request, *args, **kwargs)


class AdminProviderListView(AdminRequiredMixin, ListView):
    """View for listing all providers (admin only)."""
    
    model = Provider
    template_name = 'admin/provider_list.html'
    context_object_name = 'providers'
    paginate_by = 50
    
    def get_queryset(self):
        """Get all providers with annotations."""
        from reviews.models import Review
        
        queryset = Provider.objects.select_related('user').all()
        
        # Add service count
        queryset = queryset.annotate(service_count=Count('services', distinct=True))
        
        # Search by email
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(user__email__icontains=search)
        
        # Filter by status
        status = self.request.GET.get('status', '').strip()
        if status and status in ['active', 'inactive', 'suspended']:
            queryset = queryset.filter(subscription_status=status)
        
        # Order by email
        queryset = queryset.order_by('user__email')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add search/filter info to context."""
        context = super().get_context_data(**kwargs)
        
        # Add search and filter values
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['status_choices'] = ['active', 'inactive', 'suspended']
        
        # Calculate statistics for each provider
        from reviews.models import Review
        providers_with_stats = []
        for provider in context['providers']:
            reviews = Review.objects.filter(provider=provider)
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] if reviews.exists() else 0
            providers_with_stats.append({
                'provider': provider,
                'review_count': reviews.count(),
                'avg_rating': avg_rating
            })
        context['providers_with_stats'] = providers_with_stats
        
        return context


class ProviderSubscriptionView(ProviderRequiredMixin, FormView):
    """View for managing provider subscriptions."""
    
    form_class = SubscriptionSettingsForm
    template_name = 'providers/subscription.html'
    success_url = reverse_lazy('subscription_confirm')
    
    def get_context_data(self, **kwargs):
        """Add provider to context."""
        context = super().get_context_data(**kwargs)
        try:
            provider = Provider.objects.get(user=self.request.user)
            context['provider'] = provider
        except Provider.DoesNotExist:
            context['provider'] = None
        return context
    
    def form_valid(self, form):
        """Handle form submission and activate subscription."""
        from payments.models import SubscriptionPayment
        
        payment_method = form.cleaned_data['payment_method']
        
        try:
            provider = Provider.objects.get(user=self.request.user)
            
            # Create SubscriptionPayment record
            subscription_payment = SubscriptionPayment.objects.create(
                provider=provider,
                amount=29.99,  # Monthly subscription cost
                payment_method=payment_method,
                status='pending'
            )
            
            # Activate subscription
            provider.activate_subscription(payment_method)
            
            # Send confirmation email
            self._send_subscription_confirmation_email(provider, payment_method)
            
            messages.success(
                self.request,
                'Subscription activated! Please complete payment to activate your services.'
            )
        except Provider.DoesNotExist:
            messages.error(self.request, 'Provider profile not found.')
            return redirect('provider_profile')
        
        return super().form_valid(form)
    
    def _send_subscription_confirmation_email(self, provider, payment_method):
        """Send subscription confirmation email."""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        
        try:
            html_message = render_to_string('emails/subscription_confirmation.html', {
                'provider': provider,
                'amount': 29.99,
                'payment_method_display': dict(SubscriptionSettingsForm.PAYMENT_METHOD_CHOICES).get(payment_method, payment_method),
                'renewal_date': provider.subscription_renewal_date,
            })
            
            send_mail(
                'Subscription Activated - Massage Marketplace',
                'Your subscription has been activated.',
                'noreply@massagemarketplace.com',
                [provider.user.email],
                html_message=html_message,
                fail_silently=True
            )
        except Exception:
            # Silently fail if email cannot be sent
            pass


class SubscriptionConfirmView(ProviderRequiredMixin, TemplateView):
    """View to confirm subscription activation."""
    
    template_name = 'providers/subscription_confirm.html'
    
    def get_context_data(self, **kwargs):
        """Add provider and payment info to context."""
        context = super().get_context_data(**kwargs)
        try:
            provider = Provider.objects.get(user=self.request.user)
            context['provider'] = provider
            
            # Get the most recent subscription payment
            from payments.models import SubscriptionPayment
            recent_payment = SubscriptionPayment.objects.filter(
                provider=provider
            ).order_by('-created_at').first()
            context['recent_payment'] = recent_payment
        except Provider.DoesNotExist:
            context['provider'] = None
        return context
