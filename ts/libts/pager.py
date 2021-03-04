# -*- coding: utf-8 -*-
"""
Pager class
"""


class Pager(object):
    """
    A class for creating pagers on pages.
    """

    PAGE_RANGE = 5

    def __init__(self, request, objects):
        self.pages = []
        self.page = {}
        self.__objects = objects
        self.__request = request
        self.around = []
        self.per_page = 20

    def update(self):
        """
        Updates the number of pages after changing the source objects.
        """

        if hasattr(self.__objects, 'count'):
            num_objects = self.__objects.count()
        else:
            num_objects = len(self.__objects)

        num_pages = int(num_objects/self.per_page)

        if num_objects % self.per_page > 0:
            num_pages += 1

        self.pages = range(1, num_pages + 1)

    def get_page(self):
        """
        Returns a "single page" of objects.
        """

        self.update()

        page_number = int(self.__request.GET.get('p', 1))

        num_from = (page_number - 1)*int(self.per_page)
        num_to = page_number*int(self.per_page)

        self.page['current'] = page_number
        self.page['first'] = 1

        if len(self.pages) > 0:
            self.page['last'] = self.pages[-1]

        self.page['previous'] = page_number - 1
        self.page['next'] = page_number + 1

        self.pages_around()

        return self.__objects[num_from:num_to]

    def pages_around(self):
        """
        Sets self.around which is a range of page numbers around
        the current one. This is used when you don't want to have
        500+ page buttons, but rather 1 +- PAGE_RANGE.
        """

        num_from = self.page['current'] - self.PAGE_RANGE - 1

        if self.page['current'] <= self.PAGE_RANGE:
            num_from = 0
            num_to = self.PAGE_RANGE + self.page['current']
        elif self.page['current'] > self.page['last'] - self.PAGE_RANGE:
            num_to = self.page['last']
        else:
            num_to = self.page['current'] + self.PAGE_RANGE

        self.around = self.pages[num_from:num_to]
