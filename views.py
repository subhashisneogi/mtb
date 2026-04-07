from django.shortcuts import render
from django.conf import settings
from django.core.paginator import Paginator
from rest_framework.exceptions import APIException, ValidationError

@permission_required_admin
def users_profile_list(request):
    """Users list for Superadmin (Template View)"""

    USER_TYPE_CONFIG = {
        "grower": {
            "model": GrowerProfile,
            "serializer": GrowerProfileSerializer,
        },
        "aggregator": {
            "model": AggregatorProfile,
            "serializer": AggregatorProfileSerializer,
        },
        "blf": {
            "model": BlfProfile,
            "serializer": BlfProfileSerializer,
        },
    }

    # ✅ Get params
    user_type = request.GET.get('user_type')
    if not user_type:
        raise APIException({'msg': "User type required"})

    config = USER_TYPE_CONFIG.get(user_type)
    if not config:
        raise ValidationError({"msg": "Invalid user_type"})

    model = config["model"]
    serializer_class = config["serializer"]

    id = request.GET.get('id')
    all_data = request.GET.get('all')
    order_by = request.GET.get('order_by', '-id')

    # ✅ Filters
    search = {}
    search = custom_filters(request, search, ['user_type'])

    # ✅ Single record
    if id:
        obj = model.cmobjects.filter(id=id).first()
        serializer = serializer_class(obj)
        context = {"data": serializer.data}
        return render(request, 'profile/user_list.html', context)

    # ✅ Queryset
    queryset = model.cmobjects.filter(*search).order_by(*order_by.split(","))

    # ✅ All data (no pagination)
    if all_data == 'true':
        serializer = serializer_class(queryset, many=True)
        context = {"data": serializer.data}
        return render(request, 'profile/user_list.html', context)

    # ✅ Pagination
    page_size = int(request.GET.get('page_size', settings.MIN_PAGE_SIZE))
    paginator = Paginator(queryset, page_size)

    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    serializer = serializer_class(page, many=True)

    context = {
        "data": serializer.data,
        "count": paginator.count,
        "next": page.next_page_number() if page.has_next() else None,
        "previous": page.previous_page_number() if page.has_previous() else None,
        "user_type": user_type
    }

    return render(request, 'profile/user_list.html', context)
