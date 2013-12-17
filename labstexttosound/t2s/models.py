from django.db import models
import datetime

# Create your models here.

class Tweet(models.Model):
    group_key = models.CharField(max_length=50, blank=False)
    tweet_id = models.BigIntegerField()
    from_user = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=50)
    raw_text = models.CharField(max_length=250)
    parsed_text = models.CharField(max_length=250)
    tweet_created_at = models.DateTimeField(default=datetime.datetime.now, blank=True)
    profile_image_url = models.CharField(max_length=250)
    url = models.CharField(max_length=250)
    status = models.CharField(max_length=15)    # Hack: This should be an enum type.
    mood = models.CharField(max_length=250)

    def __unicode__(self):
        return self.parsed_text
