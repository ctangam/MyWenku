from django.db import models
from django.contrib.auth.models import User


class Channel(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    def get_files_count(self):
        return File.objects.filter(second_category__first_category__channel=self).count()

    def get_files(self):
        return File.objects.filter(second_category__first_category__channel=self)

    def get_latest_files(self):
        return File.objects.filter(second_category__first_category__channel=self).order_by('-uploaded_at')[0:5]

    def get_hotest_files(self):
        return File.objects.filter(second_category__first_category__channel=self).order_by('-views')[0:9]

    def get_first_categories(self):
        return First_Category.objects.filter(channel=self)


class First_Category(models.Model):
    name = models.CharField(max_length=20)
    channel = models.ForeignKey(Channel, related_name='first_categories')

    def __str__(self):
        return self.name

    def get_files_count(self):
        return File.objects.filter(second_category__first_category=self).count()

    def get_files(self):
        return File.objects.filter(second_category__first_category=self)

    def get_latest_files(self):
        return File.objects.filter(second_category__first_category=self).order_by('-uploaded_at')[0:5]

    def get_hotest_files(self):
        return File.objects.filter(second_category__first_category=self).order_by('-views')[0:9]

    def get_second_categories(self):
        return Second_Category.objects.filter(first_category=self)


class Second_Category(models.Model):
    name = models.CharField(max_length=20)
    first_category = models.ForeignKey(First_Category, related_name='second_categories')

    def __str__(self):
        return self.name

    def get_files_count(self):
        return File.objects.filter(second_category=self).count()

    def get_files(self):
        return File.objects.filter(second_category=self)

    def get_latest_files(self):
        return File.objects.order_by('-uploaded_at')[0:5]

    def get_hotest_files(self):
        return File.objects.order_by('-views')[0:9]


class File(models.Model):

    name = models.CharField(max_length=30)
    title = models.CharField(max_length=30)
    description = models.CharField(max_length=400)
    content = models.TextField()
    ext = models.CharField(max_length=10)
    status = models.IntegerField(choices=((1, 'Normal'), (0, 'Converting'), (-1, 'Deleted'), (-2, 'FileDeleted')), default=1)
    page = models.PositiveIntegerField(null=True)
    MD5 = models.CharField(max_length=50)
    size = models.CharField(max_length=30)
    views = models.PositiveIntegerField(default=0)
    collects = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    file = models.FileField(upload_to='file', null=True)
    pdf_path = models.FileField(max_length=100, null=True)
    img_path = models.CharField(max_length=100, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, related_name='uploads')
    collected_by = models.ManyToManyField(User, related_name='collects', null=True)
    second_category = models.ForeignKey(Second_Category, related_name='files')


    def __str__(self):
        return self.name

    def get_latest_files(self):
        return File.objects.order_by('-uploaded_at')[0:3]

    def get_hotest_files(self):
        return File.objects.order_by('-views')[0:3]

    def get_files_count(self):
        return File.objects.all().count()

class SearchLog(models.Model):
    keyword = models.CharField(max_length=30)
    times = models.PositiveIntegerField(default=0)



