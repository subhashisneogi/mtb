"""
Common mixin and decorators created BY @Subhashis Neogi
"""

import datetime
from django.views import generic
from django.shortcuts import render
from django.db.models import Sum, Value, Count
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
User = get_user_model()

from user_profile.models import *
from .models import *



class CommonMixin(generic.base.ContextMixin):
	"""
	Common Mixin (used for footer elements)
	"""

	@staticmethod
	def update_common_context(user, context):
		"""
		Updates Common context for footer elements
		"""    
		id = user.id
		context['usertype_list'] = ProfileType.objects.exclude(name="ADMIN").order_by('-id')
		context['blf_details'] = BlfProfile.objects.filter(user_id=id).first()
		user_details = Profile.objects.filter(user_id=id).first()
		context['logged_user_type'] = str(user_details.user_type)

	def get_context_data(self, **kwargs):
		context = super(CommonMixin, self).get_context_data(**kwargs)
		CommonMixin.update_common_context(self.request.user, context)
		return context

	@staticmethod
	def render(request, template, context):
		"""
		Updates common context and render using the template supplied(Mainly used for Function-Based Views)
		"""
		CommonMixin.update_common_context(request.user, context)
		return render(request, template, context)
    


