from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Event
from .forms import EventForm
from .forms import UserProfileForm
from .models import UserProfile
# For PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from .models import Event
#  Home view with search & filter
def home(request):
    query = request.GET.get('q', '')
    date_filter = request.GET.get('date', '')

    events = Event.objects.all()

    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(location__icontains=query)
        )

    if date_filter == 'upcoming':
        events = events.filter(date__gte=timezone.now().date())
    elif date_filter == 'past':
        events = events.filter(date__lt=timezone.now().date())

    events = events.order_by('-date')
    return render(request, 'home.html', {'events': events})


@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, "Event created successfully.")
            return redirect('home')
    else:
        form = EventForm()
    return render(request, 'create_event.html', {'form': form})


def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    is_registered = request.user in event.registered_users.all() if request.user.is_authenticated else False
    return render(request, 'event_detail.html', {
        'event': event,
        'is_registered': is_registered
    })


@login_required
def update_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user != event.organizer:
        messages.error(request, "You are not authorized to edit this event.")
        return redirect('home')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated successfully.")
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    return render(request, 'update_event.html', {'form': form, 'event': event})


@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user != event.organizer:
        messages.error(request, "You are not authorized to delete this event.")
        return redirect('home')

    if request.method == 'POST':
        event.delete()
        messages.success(request, "Event deleted successfully.")
        return redirect('home')

    return render(request, 'confirm_delete.html', {'event': event})


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please login.")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


# Custom LoginView with toast message
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        return super().form_valid(form)


# Register for an event with email notification
@login_required
def register_for_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.user in event.registered_users.all():
        messages.info(request, "You are already registered for this event.")
    else:
        event.registered_users.add(request.user)
        messages.success(request, "You have successfully registered for the event.")

        #  Send confirmation email
        if request.user.email:
            subject = f"Registration Confirmation: {event.title}"
            message = (
                f"Hi {request.user.username},\n\n"
                f"You have successfully registered for the event: {event.title}.\n\n"
                f"📅 Date: {event.date}\n"
                f"⏰ Time: {event.time}\n"
                f"📍 Address: {event.address}\n\n"
                f"Thank you for registering!\n"
                f"- EventFlow Team"
            )
            recipient_list = [request.user.email]
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

    return redirect('event_detail', event_id=event.id)


@login_required
def my_registrations(request):
    registered_events = request.user.registered_events.all().order_by('-date')
    return render(request, 'my_registrations.html', {'events': registered_events})


@login_required
def download_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.user not in event.registered_users.all():
        messages.error(request, "You are not registered for this event.")
        return redirect('event_detail', event_id=event.id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{event.title}_ticket.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width / 2, height - 100, "🎟 Event Ticket")

    p.setFont("Helvetica", 14)
    p.drawString(100, height - 150, f"Event: {event.title}")
    p.drawString(100, height - 170, f"Date: {event.date}")
    p.drawString(100, height - 190, f"Time: {event.time}")
    p.drawString(100, height - 210, f"Address: {event.address}")
    p.drawString(100, height - 230, f"Registered to: {request.user.username}")

    if event.qr_code:
        qr_path = event.qr_code.path
        qr_image = ImageReader(qr_path)
        p.drawImage(qr_image, width - 250, height - 320, width=100, height=100)

    p.showPage()
    p.save()

    return response


@login_required
def view_registrations(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user != event.organizer:
        messages.error(request, "Only the organizer can view registrations.")
        return redirect('home')

    registered_users = event.registered_users.all()
    return render(request, 'view_registrations.html', {
        'event': event,
        'registered_users': registered_users
    })


#  User Dashboard View (UPDATED TEMPLATE PATH)
def user_dashboard(request):
    user = request.user
    events = user.registered_events.all()
    profile = getattr(user, 'userprofile', None)

    return render(request, 'accounts/user_dashboard.html', {
        'registered_events': events,
        'profile': profile,
    })


@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('edit_profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'accounts/editprofile.html', {'profile_form': form})

@login_required
def edit_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('user_dashboard')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'accounts/edit_profile.html', {'form': form})



@login_required
def my_events(request):
    events = Event.objects.filter(organizer=request.user)
    return render(request, 'events/my_events.html', {'events': events})


@login_required
def my_events(request):
    user_events = Event.objects.filter(organizer=request.user)
    return render(request, 'events/my_events.html', {'user_events': user_events})

@login_required
def my_events(request):
    events = Event.objects.filter(organizer=request.user)
    return render(request, 'events/my_events.html', {'events': events})



@login_required
def my_events(request):
    my_created_events = Event.objects.filter(organizer=request.user)
    return render(request, 'events/my_events.html', {'my_created_events': my_created_events})
