from django.shortcuts import render
from django.utils import timezone
from django import forms
from .models import Post
from pyroutelib3 import Router
from .mapbox_token import *

router = Router("car")

class NameForm(forms.Form):
    begin_phi = forms.FloatField(
        initial=56.8874, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'begin_phi', 'step': "0.0001"}))
    begin_lambda = forms.FloatField(
        initial=35.8652, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'begin_lambda', 'step': "0.0001"}))
    end_phi = forms.FloatField(
        initial=56.8843, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'end_phi', 'step': "0.0001"}))
    end_lambda = forms.FloatField(
        initial=35.8819, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'end_lambda', 'step': "0.0001"}))


def post_list(request):
    posts = Post.objects.filter(
        published_date__lte=timezone.now()).order_by('published_date')
    ret_code = 'none'

    routeLatLons = list()
    #center_phi = (56.8874 + 56.8843) * 0.5
    #center_lambda = (35.8652 + 35.8819) * 0.5

    bound_min_phi = 56.8874
    bound_max_phi = 56.8843
    bound_min_la = 35.8652
    bound_max_la = 35.8819

    token = get_token()

    if request.method == 'POST':
        form = NameForm(request.POST)
        if form.is_valid():

            #center_phi = (form.cleaned_data['begin_phi'] + form.cleaned_data['end_phi']) * 0.5
            #center_lambda = (form.cleaned_data['begin_lambda'] + form.cleaned_data['end_lambda']) * 0.5

            bound_min_phi = form.cleaned_data['begin_phi']
            bound_max_phi = form.cleaned_data['end_phi']

            if bound_min_phi > bound_max_phi:
                temp = bound_min_phi
                bound_min_phi = bound_max_phi
                bound_max_phi = temp

            bound_min_la = form.cleaned_data['begin_lambda']
            bound_max_la = form.cleaned_data['end_lambda']

            if bound_min_la > bound_max_la:
                temp = bound_min_la
                bound_min_la = bound_max_la
                bound_max_la = temp

            start = router.findNode(
                form.cleaned_data['begin_phi'], form.cleaned_data['begin_lambda'])
            end = router.findNode(
                form.cleaned_data['end_phi'],  form.cleaned_data['end_lambda'])

            status, route = router.doRoute(start, end)
            if status == 'success':
                # Get actual route coordinates
                routeLatLons = list(map(router.nodeLatLon, route))

                for point in routeLatLons:
                    if point[0] > bound_max_phi :
                        bound_max_phi = point[0]
                    if point[0] < bound_min_phi :
                        bound_min_phi = point[0]
                    if point[1] > bound_max_la :
                        bound_max_la = point[1]
                    if point[1] < bound_min_la :
                        bound_min_la = point[1]

                ret_code = 'success'
            else:
                ret_code = status



            #ret_code =  form.cleaned_data['begin_lambda'] +  form.cleaned_data['begin_phi'] +  form.cleaned_data['end_lambda'] + form.cleaned_data['end_phi']
    else:
        form = NameForm()

    return render(request, 'blog/post_list.html', {'ret_code': ret_code, \
'form': form, 'route': routeLatLons, \
'bound_min_phi': bound_min_phi - 0.001,\
'bound_max_phi': bound_max_phi + 0.001, \
'bound_min_la': bound_min_la - 0.001,\
'bound_max_la': bound_max_la + 0.001, \
'mapbox_access_token':token  })
