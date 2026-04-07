class UserProfileAPIView(APIView):
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	USER_TYPE_CONFIG = {
		"grower": {
			"model": GrowerProfile,
			"serializer" : GrowerProfileSerializer,
		},
		"aggregator": {
			"model": AggregatorProfile,
			"serializer" : AggregatorProfileSerializer,
		},
		"blf": {
			"model": BlfProfile,
			"serializer" : BlfProfileSerializer,
		},
	}
	def get_config(self, user_type):
		config = self.USER_TYPE_CONFIG.get(user_type)
		if not config:
			raise ValidationError({"msg": "Invalid user_type"})
		return config
	def get(self, request):
		user_type = self.request.query_params.get('user_type', None)
		if not user_type:
			raise APIException({'request_status': 0, 'msg': "User type required"})
		id = self.request.query_params.get('id', None)
		all = self.request.query_params.get('all', None)
		order_by = self.request.query_params.get('order_by', '-id')
		search = {}
		search = custom_filters(self.request, search, ['user_type'])
		config = self.get_config(user_type)
		model = config["model"]
		serializer_class = config["serializer"]
		if id:
			list_data = model.cmobjects.filter(id=id).first()
			serializer = serializer_class(list_data)
			return Response(serializer.data)
		
		list_data = model.cmobjects.filter(*search).order_by(*str(order_by).split(","))
		if all == 'true':
			serializer = serializer_class(list_data, many=True)
			return Response({'results': serializer.data})
		
		page_size = int(request.query_params.get('page_size', settings.MIN_PAGE_SIZE))
		paginator = Paginator(list_data, page_size)
		page_number = self.request.query_params.get('page', 1)
		page = paginator.get_page(page_number)
		serializer = serializer_class(page, many=True)
		return Response({
			'count': paginator.count,
			'next': page.next_page_number() if page.has_next() else None,
			'previous': page.previous_page_number() if page.has_previous() else None,
			'results': serializer.data,
		})


@permission_required_admin
def users_profile_list(request):
    """Users list for Superadmin"""
    resp = UserProfileAPIView().get(request)
    _list = list(resp.data['results'])
    context = {"data": _list}
    return render(request, 'profile/user_list.html', context)


#urls.py
http://127.0.0.1:8000/users-profile-list/?user_type=grower

please write proepr users_profile_list    

