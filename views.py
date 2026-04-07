@permission_required_admin
def users_profile_list(request):
    factory = APIRequestFactory()

    drf_request = factory.get('/users-profile-list/', data=request.GET)
    drf_request.user = request.user

    # pass auth header if exists
    if request.META.get('HTTP_AUTHORIZATION'):
        drf_request.META['HTTP_AUTHORIZATION'] = request.META['HTTP_AUTHORIZATION']

    response = UserProfileAPIView.as_view()(drf_request)

    data = response.data

    return render(request, 'profile/user_list.html', {
        "data": data.get("results", data),
        "count": data.get("count"),
        "next": data.get("next"),
        "previous": data.get("previous"),
    })
