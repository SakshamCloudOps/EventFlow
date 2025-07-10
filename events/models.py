from django.db import models
from django.contrib.auth.models import User
import qrcode
from io import BytesIO
from django.core.files import File
from django.db.models.signals import post_save
from django.dispatch import receiver


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    map_link = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    pdf = models.FileField(upload_to='event_pdfs/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE)
    registered_users = models.ManyToManyField(User, related_name='registered_events', blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        qr = qrcode.make(f"http://127.0.0.1:8000/event/{self.id}/")
        canvas = BytesIO()
        qr.save(canvas, format='PNG')
        fname = f'qr_code_{self.id}.png'
        self.qr_code.save(fname, File(canvas), save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


#  Enhanced UserProfile model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    education = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], blank=True)
    birth_date = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    instagram = models.URLField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Automatically create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
