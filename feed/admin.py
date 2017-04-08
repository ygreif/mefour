from django.contrib import admin
import models
# Register your models here.
# admin.site.register(models.Story)


@admin.register(models.Story)
class StoryAdmin(admin.ModelAdmin):
    date_hierarchy = 'pub_date'
