from django.db import models

class HomePortfolio(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    img = models.ImageField(upload_to='media')
    items = [1,2,3,4,5,6,7,8,9]

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        verbose_name_plural = 'Portfolio'
