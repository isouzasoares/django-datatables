# -*- coding: utf-8 -*-
import json
import operator
from functools import reduce

from django.views.generic import ListView
from django.http import HttpResponse
from django.db.models import Q


class DataTables(ListView):
    form_class = None

    def get_item(self, item):
        return []

    def get_columns_names(self):
        return []

    def get_columns(self):
        return []

    def search(self, query=None):
        qs = self.get_queryset()
        if query:
            search_items = {}
            for column in self.get_columns():
                if column:
                    search_items["%s__icontains" % column] = query
            q_list = [Q(x) for x in search_items.items()]
            q_list = reduce(operator.or_, q_list)
            qs = qs.filter(q_list)
        return qs

    def get_checkbox(self, pk):
        check_item = "<input type='checkbox' id='%s' class='check_item'/>"
        return check_item % pk

    def get_context_data(self, **kwargs):
        context = super(DataTables, self).get_context_data(**kwargs)
        context["columns"] = self.get_columns_names()
        context["form"] = self.form_class
        return context

    def get_order_column(self, order_column, order_type):
        order_by = None
        if order_column:
            columns = self.get_columns()
            try:
                column = columns[int(order_column)]
                if column:
                    order_by = column
                    if order_type == "desc":
                        order_by = "-%s" % order_by
            except:
                return order_by

        return order_by

    def get_buttons(self, array_buttons):
        """
        Generate buttons for use in each table row.

        array_buttons: array of objects
        **object style: url: the url for go to,
                        class_name: classes for the element,
                        label: string label for element
                        icon: icon classes for element

        return: array of html 'a' elements
        """
        mount_buttons = []
        bt_template = '<a href="%s" class="%s">%s</a>'
        for item in array_buttons:
            icon_tp = '<i class="%s"></i> '
            label_txt = (icon_tp % (item['icon'])) if 'icon' in item else ''
            label_txt += item['label'] if 'label' in item else ''

            mount_buttons.append(bt_template % (
                item['url'] if 'url' in item else '',
                item['class_name'] if 'class_name' in item else '',
                label_txt
            ))
        return ' '.join(mount_buttons)

    def get_obj(self, qs, offset=0, limit=10, order_by=None):
        if order_by:
            qs = qs.order_by(order_by)
        count = qs.count()
        list_item = []
        qs = qs[offset:limit + offset]
        for item in qs:
            list_item.append(self.get_item(item))
        return {"data": list_item,
                "recordsTotal": count,
                "recordsFiltered": count}

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            offset = int(request.GET.get('start', 0))
            limit = int(request.GET.get('length', 10))
            order = self.get_order_column(request.GET.get('order[0][column]'),
                                          request.GET.get('order[0][dir]'))
            qs = self.search(request.GET.get("search[value]"))
            qs = self.get_obj(qs, offset, limit, order)
            return HttpResponse(json.dumps(qs))
        return super(DataTables, self).get(request, *args, **kwargs)


class PostAjaxMixin(object):

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            try:
                self.object = self.get_object()
            except:
                self.object = None
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            if form.is_valid():
                form.save()
                return HttpResponse(json.dumps({"sucess": 1}),
                                    'application/json')
            else:
                return HttpResponse(json.dumps({"error": form.errors.as_ul()}),
                                    'application/json')
