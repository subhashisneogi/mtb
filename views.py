class GrowerProfileUpdateView(LoginRequiredMixin, CommonMixin, UpdateView,):
	"""
	Grower Profile Update View 
	"""
	model = GrowerProfile
	form_class = GrowerProfileForm
	second_form_class = CreateUserFormedit
	template_name = 'profile/grower_profile_update.html'

	def get(self, request, *args, **kwargs):
	# checking if the user is Admin
		try:
			if not self.request.user.is_superuser:
				messages.error(self.request, 'You have no permission to access the requested resource!')
				return redirect(reverse('index'))
		except AttributeError as error:
			messages.error(self.request, 'You have no permission to access the requested resource!')
			return redirect(reverse('index'))
		return super().get(request, *args, **kwargs)

	def get_success_url(self, **kwargs):
		messages.success(self.request, 'Grower Profile Updated Successfully')
		return reverse('user_profile:all_users',kwargs={"usertype_slug": 'grower' }) 

	def get_object(self):
		profile_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['user_create_pk']).first()
		return profile_details

	def get_context_data(self, **kwargs):
		kwargs['active_client'] = True
		if 'form' not in kwargs:
			kwargs['form'] = self.form_class(instance=self.get_object())
		if 'form2' not in kwargs:
			kwargs['form2'] = self.second_form_class(instance=self.get_object().user)

		context = super(GrowerProfileUpdateView, self).get_context_data(**kwargs)
		context['aggregator_list'] = AggregatorProfile.cmobjects.all().order_by('-id')
		context['profile_details'] = self.get_object()
		return context
	
	def form_valid(self, form, ):
		
		self.user_id = self.kwargs['user_create_pk']

		context = self.get_context_data()

		profile_details = GrowerProfile.cmobjects.filter(user_id=self.kwargs['user_create_pk']).first()

		print("Profile Details", profile_details)

		garden_details = Gardens.objects.filter(grower_id=profile_details.pk).first()

		Gardens.objects.filter(grower_id=profile_details.pk).update(name = form.instance.name)

		print("GARDEN DETAILS###", garden_details)

		Plot.objects.filter(garden_id=garden_details.pk).update_or_create(garden_id=garden_details.pk, defaults={
			'name': form.instance.name,})

		GrowerQrCode.objects.update_or_create(grower_id=form.instance.pk, \
					defaults={'name': form.instance.name,})

		with transaction.atomic():
			self.object = form.save()

		return super(GrowerProfileUpdateView, self).form_valid(form)
