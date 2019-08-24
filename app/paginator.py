import math

from app import app


class Paginator:
    def __init__(self, object_list, num_per_page=None):
        self.object_list = object_list
        self.num_per_page = num_per_page
        if num_per_page is None:
            self.num_per_page = app.config['NUM_PER_PAGE']

    def _get_page(self, object_list, num_page):
        return Page(object_list, num_page, self)

    def page(self, num_page):
        num_page = int(num_page)
        bottom = (num_page - 1) * self.num_per_page
        top = bottom + self.num_per_page
        object_list = self.object_list[bottom:top]
        return self._get_page(object_list, num_page)

    @property
    def count(self):
        return len(self.object_list)

    @property
    def num_pages(self):
        return math.ceil(self.count / self.num_per_page)


class Page:
    def __init__(self, object_list, num_page, paginator):
        self.paginated = object_list
        self.num_page = num_page
        self.paginator = paginator

    @property
    def has_other(self):
        return self.paginator.num_pages != 1

    @property
    def has_next(self):
        return self.num_page < self.paginator.num_pages

    @property
    def has_prev(self):
        return self.num_page > 1

    @property
    def next_num(self):
        if self.has_next:
            return self.num_page + 1
        return False

    @property
    def prev_num(self):
        if self.has_prev:
            return self.num_page - 1
        return False

    @property
    def last(self):
        return self.paginator.num_pages
