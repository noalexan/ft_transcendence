from django.db import models
from django.utils import timezone
from random_username.generate import generate_username

def random_username():
  return generate_username()[0]

# Create your models here.
class User(models.Model):
  nickname = models.CharField(max_length=30, default=random_username)

  fortytwo_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
  github_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
  discord_id = models.CharField(max_length=255, unique=True, blank=True, null=True)

  dfa_secret = models.CharField(max_length=50, null=True)

  created_at = models.DateTimeField(auto_now_add=True)