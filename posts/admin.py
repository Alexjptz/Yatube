from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        '__str__',
        'text',
        'pub_date',
        'author',
        'group',
        'image'
    )
    search_fields = ('text',)
    list_filter = ('pub_date', 'group',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'slug',
        'description'
    )
    search_fields = ('title',)
    empty_value_display = '--пусто--'


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'post',
        'author',
        'text',
        'created'
    )
    search_fields = ('author, post',)
    list_filter = ('created',)
    empty_value_display = '--пусто--'


class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'author'
    )
    search_fields = ('user', 'author',)
    list_filter = ('user', 'author',)
    empty_value_display = '--пусто--'


admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
