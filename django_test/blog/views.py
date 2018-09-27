from django.shortcuts import render
from django.utils import timezone
from django import forms
from .models import Post

test_data = "initial"

class NameForm(forms.Form):
    your_name = forms.CharField(label='Your name', max_length=100)

def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    test_data = "first_pressed"

    if request.method == 'POST':
        form = NameForm(request.POST)
        test_data = "check_post"
        if form.is_valid():
            test_data = "is_valid"
            test_data = form.cleaned_data['your_name']

    return render(request, 'blog/post_list.html', {'posts': posts,'test_data': test_data})
