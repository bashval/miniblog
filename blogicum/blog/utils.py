from datetime import datetime
from django.db.models import Count, Q, QuerySet


def get_published_or_author_posts(model, author_id=None) -> QuerySet:
    """Returns all objects that are published or have author with 'author_id'.
    Adds comment_count to resuletd queryset.
    """
    queryset = model.objects.filter(
        Q(author_id=author_id) | (
            Q(pub_date__lt=datetime.now())
            & Q(is_published=True)
            & Q(category__is_published=True)
        ),
    ).annotate(
        comment_count=Count('comments')
    )
    return queryset
