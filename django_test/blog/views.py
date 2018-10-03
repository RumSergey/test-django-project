from django.shortcuts import render
from django.utils import timezone
from django import forms
from .models import Post
from pyroutelib3 import Router
router = Router("foot")

center_phi = (56.8874 + 56.8843) * 0.5
center_lambda = (35.8652 + 35.8819) * 0.5


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

    if request.method == 'POST':
        form = NameForm(request.POST)
        if form.is_valid():

            center_phi = (form.cleaned_data['begin_phi'] + form.cleaned_data['end_phi']) * 0.5
            center_lambda = (form.cleaned_data['begin_lambda'] + form.cleaned_data['end_lambda']) * 0.5

            start = router.findNode(
                form.cleaned_data['begin_phi'], form.cleaned_data['begin_lambda'])
            end = router.findNode(
                form.cleaned_data['end_phi'],  form.cleaned_data['end_lambda'])

            status, route = router.doRoute(start, end)
            if status == 'success':
                # Get actual route coordinates
                routeLatLons = list(map(router.nodeLatLon, route))
                ret_code = 'success'
            else:
                ret_code = status

            #ret_code =  form.cleaned_data['begin_lambda'] +  form.cleaned_data['begin_phi'] +  form.cleaned_data['end_lambda'] + form.cleaned_data['end_phi']
    else:
        form = NameForm()

    return render(request, 'blog/post_list.html', {'ret_code': ret_code, 'form': form, 'route': routeLatLons, 'center_phi': center_phi,'center_lambda': center_lambda })
