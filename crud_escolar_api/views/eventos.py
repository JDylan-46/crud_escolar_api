from django.shortcuts import render
from django.db.models import *
from django.db import transaction
from crud_escolar_api.serializers import *
from crud_escolar_api.models import *
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.generics import CreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from django.core import serializers
from django.utils.html import strip_tags
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string
import string
import random
import json

class EventosAll(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EventosSerializer

    def get_queryset(self):
        return Eventos.objects.order_by("id")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        lista = self.get_serializer(queryset, many=True).data
        # Convierte publico_json de string a array
        for evento in lista:
            try:
                evento["publico_json"] = json.loads(evento["publico_json"])
            except Exception:
                evento["publico_json"] = []
        return Response(lista, 200)

class EventosView(generics.CreateAPIView):
    #permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        evento_obj = get_object_or_404(Eventos, id=request.GET.get("id"))
        evento = EventosSerializer(evento_obj, many=False).data

    # Decodificar JSON
        try:
            evento["publico_json"] = json.loads(evento["publico_json"])
        except Exception:
            evento["publico_json"] = []

        # Buscar ID del responsable (si es string y necesitas ID)
        nombre_resp = evento_obj.responsable.strip()
        evento["responsable_id"] = None

        if nombre_resp:
            partes = nombre_resp.split(" ")
            if len(partes) >= 2:
                nombre = partes[0]
                apellido = partes[1]

                maestro = Maestros.objects.filter(user__first_name=nombre, user__last_name=apellido).first()
                if maestro:
                    evento["responsable_id"] = maestro.id
                else:
                    admin = Administradores.objects.filter(user__first_name=nombre, user__last_name=apellido).first()
                    if admin:
                        evento["responsable_id"] = admin.id

        return Response(evento, 200)


    #Registrar nuevo evento
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        if isinstance(data.get("publico_json"), list):
            data["publico_json"] = json.dumps(data["publico_json"])

        responsable_id = data.get("responsable")
        nombre_responsable = ""
        maestro = Maestros.objects.filter(id=responsable_id).first()
        if maestro:
            nombre_responsable = f"{maestro.user.first_name} {maestro.user.last_name}"
        else:
            admin = Administradores.objects.filter(id=responsable_id).first()
            if admin:
                nombre_responsable = f"{admin.user.first_name} {admin.user.last_name}"
        data["responsable"] = nombre_responsable


        even = EventosSerializer(data=data)
        if even.is_valid():
            evento = even.save()
            return Response({"evento_created_id": evento.id}, 201)
        return Response(even.errors, status=status.HTTP_400_BAD_REQUEST)

class EventosViewEdit(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        evento = get_object_or_404(Eventos, id=request.data["id"])
        evento.nombreEv = request.data["nombreEv"]
        evento.tipo_evento = request.data["tipo_evento"]
        evento.fecha_realizacion = request.data["fecha_realizacion"]
        evento.horaInicio = request.data["horaInicio"]
        evento.horaFin = request.data["horaFin"]
        evento.lugar = request.data["lugar"]
        responsable_id = request.data["responsable"]
        nombre_responsable = ""
        maestro = Maestros.objects.filter(id=responsable_id).first()
        if maestro:
            nombre_responsable = f"{maestro.user.first_name} {maestro.user.last_name}"
        else:
            admin = Administradores.objects.filter(id=responsable_id).first()
            if admin:
                nombre_responsable = f"{admin.user.first_name} {admin.user.last_name}"
        evento.responsable = nombre_responsable
        evento.publico_json = json.dumps(request.data["publico_json"])
        evento.programa_educativo = request.data["programa_educativo"]
        evento.descripcion_breve = request.data["descripcion_breve"]
        evento.cupo = request.data["cupo"]
        evento.save()
        
        even = EventosSerializer(evento, many=False).data

        return Response(even, 200)

    def delete(self, request, *args, **kwargs):
        profile = get_object_or_404(Eventos, id=request.GET.get("id"))
        try:
            profile.delete()
            return Response({"details": "Evento eliminado"}, 200)
        except Exception as e:
            return Response({"details": "Algo pasó al eliminar"}, 400)