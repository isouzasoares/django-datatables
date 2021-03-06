# -*- coding: utf-8 -*-
import json
import operator
from functools import reduce

from django.views.generic import ListView, DeleteView
from django.http import HttpResponse, JsonResponse
from django.db.models import Q


class DataTables(ListView):
    title = "Lista default"
    form_class = None
    searchable = True

    def get_queryset(self):
        qs = super(DataTables, self).get_queryset()
        if self.form_class:
            form = self.form_class(self.request.GET)
            qs = form.filtrar(qs)
        return qs

    def get_item(self, item):
        return []

    def get_columns_names(self):
        return []

    def get_columns(self):
        if self.model:
            return [
                field.get_attname() for field in self.model._meta.get_fields()
                if hasattr(field, 'get_attname') and not field.related_model
            ]
        else:
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
        context["title"] = self.title
        context["model"] = self.model
        context['searchable'] = self.searchable
        context['urls_form'] = {}
        if self.form_class:
            urls_form = getattr(self.form_class, "get_url_fields", None)
            if urls_form:
                context['urls_form'] = self.form_class.get_url_fields(None)

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

    def get_url_modal(
        self, url, modal_name="", label_name="Editar", target="", prop=""
    ):
        label_name = label_name if label_name else ""
        url_modal = '<a href="%s" class="%s" target="%s" %s>%s</a>'
        return url_modal % (url, modal_name, target, prop, label_name)

    def get_obj(self, qs, offset=0, limit=10, order_by=None):
        if order_by:
            qs = qs.order_by(order_by)
        count = qs.count()
        list_item = []
        qs = qs[offset:limit + offset]
        for item in qs:
            list_item.append(self.get_item(item))
        return {
            "data": list_item,
            "recordsTotal": count,
            "recordsFiltered": count
        }

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

    def get_format_buttons(self, buttons):
        return "<div class='btn-toolbar'>%s</div>" % buttons

    def get_delete_button(self, url_delete, text_delete="Remover"):
        h = """<button type="button" class="btn btn-danger
                   delete-item"
                   data-urldelete="%s">
                   <i class="ti-trash"></i> %s</button>"""
        return h % (url_delete, text_delete)

    def get_redirect_button(
            self, url, text='', class_icon='fa fa-arrow-right',
            class_item='btn btn-info', prop=""):
        h = """<a class="%s"
               href="%s" %s>
               <i class="%s"></i> %s</a>"""
        return h % (class_item, url, prop, class_icon, text)


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
                if getattr(form.instance, "adicionado_por", False):
                    instance = form.instance
                    instance.adicionado_por = request.user
                    instance.save()
                return HttpResponse(
                    json.dumps({
                        "sucess": 1
                    }), 'application/json')
            else:
                return HttpResponse(
                    json.dumps({
                        "error": form.errors.as_ul()
                    }), 'application/json')


class DeleteMixin(DeleteView):

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        payload = {'delete': 'ok'}
        return JsonResponse(payload)
