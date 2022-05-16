from django.conf import settings
from django.core.paginator import Paginator


def paginator(request, post_list):
    post = Paginator(post_list, settings.POSTS_COUNT)
    page_number = request.GET.get('page')
    page_obj = post.get_page(page_number)
    return page_obj
