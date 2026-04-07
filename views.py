from django.db import transaction
from django.shortcuts import redirect, reverse
from django.contrib import messages
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

class GrowerProfileUpdateView(LoginRequiredMixin, CommonMixin, UpdateView):
    """
    Grower Profile Update View (Optimized)
    """
    model = GrowerProfile
    form_class = GrowerProfileForm
    second_form_class = CreateUserFormedit
    template_name = 'profile/grower_profile_update.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Handle permission in one place instead of overriding get()
        """
        if not getattr(request.user, "is_superuser", False):
            messages.error(request, 'You have no permission to access the requested resource!')
            return redirect(reverse('index'))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        """
        Fetch object with related user in single query
        """
        return GrowerProfile.cmobjects.select_related('user').filter(
            user_id=self.kwargs['user_create_pk']
        ).first()

    def get_success_url(self):
        messages.success(self.request, 'Grower Profile Updated Successfully')
        return reverse('user_profile:all_users', kwargs={"usertype_slug": 'grower'})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile = self.object or self.get_object()

        context.update({
            'active_client': True,
            'form': kwargs.get('form') or self.form_class(instance=profile),
            'form2': kwargs.get('form2') or self.second_form_class(instance=profile.user),
            'aggregator_list': AggregatorProfile.cmobjects.all().order_by('-id'),
            'profile_details': profile
        })

        return context

    def form_valid(self, form):
        profile = self.get_object()

        if not profile:
            messages.error(self.request, "Profile not found")
            return redirect(reverse('index'))

        with transaction.atomic():
            # Save main profile
            self.object = form.save()

            # Update Garden (single query)
            garden = Gardens.objects.filter(grower_id=profile.pk).first()
            if garden:
                garden.name = form.instance.name
                garden.save(update_fields=['name'])

                # Update/Create Plot
                Plot.objects.update_or_create(
                    garden_id=garden.pk,
                    defaults={'name': form.instance.name}
                )

            # Update/Create QR Code
            GrowerQrCode.objects.update_or_create(
                grower_id=profile.pk,
                defaults={'name': form.instance.name}
            )

        return super().form_valid(form)
