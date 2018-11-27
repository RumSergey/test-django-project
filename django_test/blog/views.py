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
        time_str = time_str + "{0:d}".format(hours) + ' ч: '

    total_time = total_time - hours
    total_time = total_time * 60
    minutes = trunc( total_time )
    if hours > 0:
        time_str = time_str + "{0:d}".format(minutes) + ' мин: '
    else :
        if minutes > 0:
            time_str = time_str + "{0:d}".format(minutes) + ' мин: '

    total_time = total_time - minutes
    total_time = total_time * 60

    seconds = trunc( total_time )

    if hours > 0 or minutes > 0:
        time_str = time_str + "{0:d}".format(seconds) + ' сек'
    else :
        if seconds > 0:
            time_str = time_str + "{0:d}".format(seconds) + ' сек'
        else:
            time_str = time_str + "{0:0.2f}".format(total_time) + ' сек'

    return time_str

def time_to_start_str(total, form_h, form_m):
    if form_h == 0 and form_m == 0:
        return ''
    else :

        count_hours = trunc( total )
        total_time = total - count_hours
        total_time = total_time * 60
        count_minutes = trunc( total_time )

        ret_m = 0

        if form_m >= count_minutes :
            ret_m = form_m - count_minutes
        else :
            ret_m = 60 - (count_minutes - form_m)
            count_hours = count_hours + 1

        ret_h = form_h - count_hours

        if ret_h < 0:
            ret_h = 24 - (count_hours - form_h)

        ret = ', время старта ' + "{0:d}".format(ret_h) + ' ч: ' + "{0:d}".format(ret_m) + ' мин'

        return ret

def add_delay(h1, m1, h2, m2):
    m1 = m1 - m2
    add_h = 0
    if m1 < 0:
        m1 = m1 + 60
        add_h = 1

    h1 = h1 - h2 - add_h

    if h1 < 0:
        h1 = h1 + 24

    return (h1,m1)


class NameForm(forms.Form):
    techlist = (
            ('car', 'Автомобиль'),
            ('cycle', 'Велосипед'),
            ('foot', 'Пешком'),
            ('horse', 'Лошадь'),
            ('tram', 'Трамвай'),
            ('train', 'Поезд')
        )


    begin_phi = forms.FloatField(label="Точка выхода, широта",
        initial=56.8874, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'begin_phi', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    begin_lambda = forms.FloatField(label="Точка выхода, долгота",
        initial=35.8652, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'begin_lambda', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    med_phi = forms.FloatField(label="Склад, широта",
        initial=56.8856, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'med_phi', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    med_lambda = forms.FloatField(label="Склад, долгота",
        initial=35.8712, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'med_lambda', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    end_phi = forms.FloatField(label="Точка встречи, широта",
        initial=56.8843, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'end_phi', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    end_lambda = forms.FloatField(label="Точка встречи, долгота",
        initial=35.8819, required='True', max_value=90.0, min_value=-90.0,widget=forms.NumberInput(attrs={'id': 'end_lambda', 'step': "0.0001", 'onchange' : "onInputChanged()"}))
    wheel_val = forms.ChoiceField(choices=techlist,label="Вид транспорта", initial='car', required=True, widget=forms.Select(attrs={'id': 'wheel_val'}))
    arrival_time_hour = forms.IntegerField(label="Время прибытия, ч",
        required='False', initial=0, min_value=0, max_value=24, widget=forms.NumberInput(attrs={'id': 'arr_time_hour', 'step': "1", 'onchange' : "onInputChanged()"}))
    arrival_time_minutes = forms.IntegerField(label="Время прибытия, м",
        required='False', initial=0, min_value=0, max_value=60, widget=forms.NumberInput(attrs={'id': 'arr_time_minutes', 'step': "1", 'onchange' : "onInputChanged()"}))
    sclad_time_hour = forms.IntegerField(label="Ожидание на складе, ч",
        required='False', initial=0, min_value=0, max_value=24, widget=forms.NumberInput(attrs={'id': 'sclad_time_hour', 'step': "1", 'onchange' : "onInputChanged()"}))
    sclad_time_minutes = forms.IntegerField(label="Ожидание на складе, м",
        required='False', initial=0, min_value=0, max_value=60, widget=forms.NumberInput(attrs={'id': 'sclad_time_minutes', 'step': "1", 'onchange' : "onInputChanged()"}))



def post_list(request):
    posts = Post.objects.filter(
        published_date__lte=timezone.now()).order_by('published_date')
    ret_code = 'none'
    timing = ''

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
            ar_time_h = form.cleaned_data['arrival_time_hour']
            ar_time_m = form.cleaned_data['arrival_time_minutes']
            scl_time_h = form.cleaned_data['sclad_time_hour']
            scl_time_m = form.cleaned_data['sclad_time_minutes']

            print('before')
            print(ar_time_h,ar_time_m)
            print('scl_time_h',scl_time_h)
            ar_time_h,ar_time_m = add_delay(ar_time_h,ar_time_m,scl_time_h,scl_time_m)
            print('after')
            print(ar_time_h,ar_time_m)


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
            time_str_1 = ''
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
                ret_code = 'Результаты расчетов: время в пути до склада '
                time_str_1 = hours_to_time_str(sum_length / speed_list[transport])
                ret_code = ret_code + time_str_1
            else:
                if ret_code == 'none':
                    ret_code = 'Результаты расчетов: маршрут до склада отсутствует, '
                else:
                    ret_code = 'Результаты расчетов: маршрут до склада не построен, '

            status, route = router.doRoute(med, end)
            sum_length2 = 0
            time_str_2 = ''

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
                ret_code = ret_code + '; время в пути до точки встречи '
                time_str_2 = hours_to_time_str(sum_length2 / speed_list[transport])
                ret_code = ret_code + time_str_2
            else:
                if ret_code == 'none':
                    ret_code = 'маршрут до точки встречи отсутствует, '
                else:
                    ret_code = 'маршрут до точки встречи не построен, '

            ret_code = ret_code + '; общая длина маршрута ' +  "{0:.2f}".format(sum_length + sum_length2)  + ' км'
            ret_code = ret_code + ', время движения ' +  hours_to_time_str((sum_length + sum_length2) / speed_list[transport])
            #ret_code = ret_code + ' ( ' + time_str_1 + ' до склада, ' + time_str_2 + ' до точки встречи)'
            ret_code = ret_code + time_to_start_str( (sum_length + sum_length2) / speed_list[transport], ar_time_h,ar_time_m)
            timing = 'Время выполнения расчётов: ' + "{0:.2f}".format(time.time() - start_time) + ' сек '


    elif request.method == 'GET':
        form = NameForm()
        ret_code = 'Введите данные'
    else:
        form = NameForm()
        ret_code = 'Неправильный http-запрос'

    return render(request, 'blog/post_list.html', {'ret_code': ret_code, \
'form': form, 'route': routeLatLons, 'routeAdd': routeLatLonsAdd,\
'bound_min_phi': bound_min_phi - 0.001,\
'bound_max_phi': bound_max_phi + 0.001, \
'bound_min_la': bound_min_la - 0.001,\
'bound_max_la': bound_max_la + 0.001, \
'timing': timing, \
'mapbox_access_token':token  })
