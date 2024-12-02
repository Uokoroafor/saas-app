from django.contrib import admin
from .models import (
    Subscription,
    UserSubscription,
    SubscriptionPrice as SubscriptionPrice_,
)


class SubscriptionPrice(admin.TabularInline):
    """
    Inline model for displaying SubscriptionPrice records in the admin interface.

    This class configures how SubscriptionPrice records are displayed within
    the Subscription model's admin interface. It makes the stripe_id field read-only,
    prevents deletion of SubscriptionPrice records, and doesn't display any extra empty forms.
    """

    model = SubscriptionPrice_
    readonly_fields = ["stripe_id"]
    can_delete = False
    extra = 0


class SubscriptionAdmin(admin.ModelAdmin):
    """
    Admin configuration for managing Subscription models.

    This class configures the admin interface for the Subscription model. It includes
    the SubscriptionPrice inline model, displays the 'name' and 'active' fields in the
    list view, and makes the 'stripe_id' field read-only.
    """

    inlines = [SubscriptionPrice]
    list_display = ["name", "active"]
    readonly_fields = ["stripe_id"]


"""
Register the Subscription and UserSubscription models with the Django admin site.
"""
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(UserSubscription)
