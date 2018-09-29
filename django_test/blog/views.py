from django.shortcuts import render
from django.utils import timezone
from django import forms
from .models import Post
from pyroutelib3 import Router
router = Router("foot")

class NameForm(forms.Form):
    begin_phi = forms.FloatField(required='True',max_value=90.0, min_value=-90.0)
    begin_lambda = forms.FloatField(required='True',max_value=90.0, min_value=-90.0)
    end_phi = forms.FloatField(required='True',max_value=90.0, min_value=-90.0)
    end_lambda = forms.FloatField(required='True',max_value=90.0, min_value=-90.0)


def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    ret_code = 'none'

    if request.method == 'POST':
        form = NameForm(request.POST)
        if form.is_valid():
            start = router.findNode(form.cleaned_data['begin_phi'], form.cleaned_data['begin_lambda'])
            end = router.findNode(form.cleaned_data['end_phi'],  form.cleaned_data['end_lambda'])

            status, route = router.doRoute(start, end)
            if status == 'success':
                routeLatLons = list(map(router.nodeLatLon, route)) # Get actual route coordinates
                ret_code = 'success'
            else :
                ret_code = status

            #ret_code =  form.cleaned_data['begin_lambda'] +  form.cleaned_data['begin_phi'] +  form.cleaned_data['end_lambda'] + form.cleaned_data['end_phi']
    else :
        form = NameForm()

    return render(request, 'blog/post_list.html', {'ret_code': ret_code,'form': form})
