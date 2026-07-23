from django.db import models

class Home(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    img = models.ImageField(upload_to='media')

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        verbose_name_plural = 'Home'
