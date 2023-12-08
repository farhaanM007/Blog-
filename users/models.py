from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """
    Model for Custom User
    """
    username=models.CharField(unique=True)
    password=models.CharField(max_length=128)
    
    USERNAME_FIELD='username'
    REQUIRED_FIELDS=['password']
    
    def __str__(self) -> str:
        return self.username

class Blog(models.Model):
    """
    Model for Blog
    """
    
    title= models.CharField(max_length=80)
    content=models.TextField()
    author=models.ForeignKey(CustomUser,on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title

class Comment(models.Model):
    """
    Model for Comment
    """
    blog=models.ForeignKey(Blog,on_delete=models.CASCADE,related_name='comments')
    name=models.CharField(max_length=80,blank=True)
    email=models.EmailField(blank=True)
    body=models.TextField()
    created_on=models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return 'Comment {} by {}'.format(self.body, self.name)
