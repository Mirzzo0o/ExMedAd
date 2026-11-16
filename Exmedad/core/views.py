from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render


@login_required
def home(request):
  return render(request, 'core/home.html')


def registro_view(request):
  if request.method == 'POST':
    form = UserCreationForm(request.POST)
    if form.is_valid():
      form.save()  
      username = form.cleaned_data.get('username')
      messages.success(
          request,
          f'¡Cuenta creada con éxito para {username}! Ya puedes iniciar'
          ' sesión.',
      )
      return redirect('login')  
  else:
    form = UserCreationForm()

  return render(request, 'core/register.html', {'form': form})
