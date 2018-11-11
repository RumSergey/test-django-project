from django.shortcuts import render
from django.utils import timezone
from django import forms
from .models import Post
from pyroutelib3 import Router
from .mapbox_token import *
import time
from math import radians, sin, cos, acos, trunc


speed_list = {'car': 30,'cycle':10,'foot':4,'horse':7,'tram':15,'train':60}

def hours_to_time_str(time_in_hours):
    total_time = time_in_hours
    hours = trunc( total_time )
    time_str = ''
    if hours > 0:
        time_str = time_str + "{0:d}".format(hours) + 'ч:'

    total_time = total_time - hours
    total_time = total_time * 60
    minutes = trunc( total_time )
    if hours > 0:
        time_str = time_str + "{0:d}".format(minutes) + 'м:'
    else :
        if minutes > 0:
            time_str = time_str + "{0:d}".format(minutes) + 'мин:'

    total_time = total_time - minutes
    total_time = total_time * 60

    seconds = trunc( total_time )

    if hours > 0 or minutes > 0:
        time_str = time_str + "{0:d}".format(seconds) + 'сек'
    else :
        if seconds > 0:
            time_str = time_str + "{0:d}".format(seconds) + 'сек'
        else:
            time_str = time_str + "{0:0.2f}".format(total_time) + 'сек'

    return time_str


class NameForm(forms.Form):
    techlist = (
            ('car', 'Автомобиль'),
            ('cycle', 'Велосипед'),
            ('foot', 'Пешком'),
            ('horse', 'Лошадь'),
            ('tram', 'Трамвай'),
            ('train', 'Поезд')
        )


    begin_phi = forms.FloatField(label="Начальная точка, широта",
        initial=56.8874, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'begin_phi', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    begin_lambda = forms.FloatField(label="Начальная точка, долгота",
        initial=35.8652, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'begin_lambda', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    med_phi = forms.FloatField(label="Промежуточная точка, широта",
        initial=56.8856, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'med_phi', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    med_lambda = forms.FloatField(label="Промежуточная точка, долгота",
        initial=35.8712, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'med_lambda', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    end_phi = forms.FloatField(label="Конечная точка, широта",
        initial=56.8843, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'end_phi', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    end_lambda = forms.FloatField(label="Конечная точка, долгота",
        initial=35.8819, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'end_lambda', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    #arrival_time = forms.TimeField(label="Требуемое время прибытия",required='False', widget=forms.TimeInput(format='%H:%M'))
    wheel_val = forms.ChoiceField(choices=techlist,label="Вид транспорта", initial='car', required=True, widget=forms.Select(attrs={'id': 'wheel_val'}))



def post_list(request):
    posts = Post.objects.filter(
        published_date__lte=timezone.now()).order_by('published_date')
    ret_code = 'none'

    routeLatLons = list()
    routeLatLonsAdd = list()
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

            bound_min_phi = form.cleaned_data['begin_phi']
            bound_max_phi = form.cleaned_data['end_phi']
            transport = form.cleaned_data['wheel_val']

            router = Router(transport)

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
            med = router.findNode(
                form.cleaned_data['med_phi'],  form.cleaned_data['med_lambda'])

            start_time = time.time()
            status, route = router.doRoute(start, med)

            sum_length = 0
            if status == 'success':
                # Get actual route coordinates
                routeLatLons = list(map(router.nodeLatLon, route))
                temp_phi = 0
                temp_la = 0

                for point in routeLatLons:
                    if point == routeLatLons[0]:
                        temp_phi = point[0]
                        temp_la = point[1]
                    else:
                        slat = radians(temp_phi)
                        slon = radians(temp_la)
                        elat = radians(point[0])
                        elon = radians(point[1])

                        dist = 6371.01 * acos(sin(slat)*sin(elat) + cos(slat)*cos(elat)*cos(slon - elon))
                        sum_length = sum_length + dist
                        temp_phi = point[0]
                        temp_la = point[1]


                    if point[0] > bound_max_phi :
                        bound_max_phi = point[0]
                    if point[0] < bound_min_phi :
                        bound_min_phi = point[0]
                    if point[1] > bound_max_la :
                        bound_max_la = point[1]
                    if point[1] < bound_min_la :
                        bound_min_la = point[1]

                #ret_code = 'success'
                #ret_code = '1-й маршрут построен, ' + 'время в пути ' + "{0:.2f}".format(sum_length / speed_list[transport]) + ' ч, '
                ret_code = '1-й маршрут построен, время в пути '
                time_str = hours_to_time_str(sum_length / speed_list[transport])
                ret_code = ret_code + time_str
            else:
                if ret_code == 'none':
                    ret_code = '1-й маршрут отсутствует, '
                else:
                    ret_code = '1-й маршрут не построен, '

            status, route = router.doRoute(med, end)
            sum_length2 = 0

            if status == 'success':
                # Get actual route coordinates
                routeLatLonsAdd = list(map(router.nodeLatLon, route))
                temp_phi = 0
                temp_la = 0

                for point in routeLatLonsAdd:
                    if point == routeLatLonsAdd[0]:
                        temp_phi = point[0]
                        temp_la = point[1]
                    else:
                        slat = radians(temp_phi)
                        slon = radians(temp_la)
                        elat = radians(point[0])
                        elon = radians(point[1])

                        dist = 6371.01 * acos(sin(slat)*sin(elat) + cos(slat)*cos(elat)*cos(slon - elon))

                        sum_length2 = sum_length2 + dist
                        temp_phi = point[0]
                        temp_la = point[1]


                    if point[0] > bound_max_phi :
                        bound_max_phi = point[0]
                    if point[0] < bound_min_phi :
                        bound_min_phi = point[0]
                    if point[1] > bound_max_la :
                        bound_max_la = point[1]
                    if point[1] < bound_min_la :
                        bound_min_la = point[1]

                #ret_code = 'success'
                ret_code = ret_code + ', 2-й маршрут построен, время в пути '
                time_str = hours_to_time_str(sum_length2 / speed_list[transport])
                ret_code = ret_code + time_str
            else:
                if ret_code == 'none':
                    ret_code = '2-й маршрут отсутствует, '
                else:
                    ret_code = '2-й маршрут не построен, '

            ret_code = ret_code + ', общая длина маршрута ' +  "{0:.2f}".format(sum_length + sum_length2)  + ' км, время расчёта ' + "{0:.2f}".format(time.time() - start_time) + ' сек '
            hours_to_time_str
            #print(speed_list[transport])
            #ret_code = ret_code + ' ,скорость' + "{0:.2f}".format(speed_list[transport])

    elif request.method == 'GET':
        form = NameForm()
        ret_code = 'ввод данных'
    else:
        form = NameForm()
        ret_code = 'неправильный http-запрос'

    return render(request, 'blog/post_list.html', {'ret_code': ret_code, \
'form': form, 'route': routeLatLons, 'routeAdd': routeLatLonsAdd,\
'bound_min_phi': bound_min_phi - 0.001,\
'bound_max_phi': bound_max_phi + 0.001, \
'bound_min_la': bound_min_la - 0.001,\
'bound_max_la': bound_max_la + 0.001, \
'mapbox_access_token':token  })
