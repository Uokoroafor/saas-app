from django.db import models
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.db.models.signals import post_save
from django.conf import settings
import helpers.billing
from django.urls import reverse

User = settings.AUTH_USER_MODEL  # auth.User

ALLOW_CUSTOM_GROUPS = True
SUBSCRIPTION_PERMISSIONS = [
    ("advanced", "Advanced Permissions"),  # subscriptions.advanced
    ("pro", "Pro Permissions"),  # subscriptions.pro
    ("basic", "Basic Permissions"),  # subscriptions.basic
    ("basic_ai", "Basic AI Permissions"),  # subscriptions.basic
]


# Create your models here.
class Subscription(models.Model):
    """Stripe Product"""

    name = models.CharField(max_length=120)
    subtitle = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    permissions = models.ManyToManyField(
        Permission,
        limit_choices_to={
            "content_type__app_label": "subscriptions",
            "codename__in": [x[0] for x in SUBSCRIPTION_PERMISSIONS],
        },
    )
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    order = models.IntegerField(default=-1, help_text="Order on Django Pricing Page")
    featured = models.BooleanField(
        default=True, help_text="Featured on Django Pricing page"
    )

    # Add Timestamps
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    features = models.TextField(
        help_text="Specify the features of each plan with each feature on a new line!",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.name}"

    class Meta:
        permissions = SUBSCRIPTION_PERMISSIONS
        ordering = ["order", "featured", "-updated"]

    def get_features_as_list(self):
        if not self.features:
            return []
        return [x.strip() for x in self.features.split("\n")]

    def save(self, *args, **kwargs):
        if not self.stripe_id:
            stripe_id = helpers.billing.create_product(
                name=self.name,
                metadata={
                    "subscription_plan_id": self.id,
                },
                raw=False,
            )
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)


class SubscriptionPrice(models.Model):
    """Stripe Price"""

    class IntervalChoices(models.TextChoices):
        MONTHLY = "month", "Monthly"
        YEARLY = "year", "Annually"

    Subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    interval = models.CharField(
        max_length=120, default=IntervalChoices.MONTHLY, choices=IntervalChoices.choices
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=9.99)
    order = models.IntegerField(default=-1, help_text="Order on Django Pricing Page")
    featured = models.BooleanField(
        default=True, help_text="Featured on Django Pricing page"
    )

    # Add Timestamps
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["Subscription__order", "order", "featured", "-updated"]

    def get_checkout_url(self):
        return reverse("sub-price-checkout", kwargs={"price_id": self.id})

    @property
    def product_stripe_id(self):
        if not self.Subscription:
            return None
        else:
            return self.Subscription.stripe_id

    @property
    def display_sub_name(self):
        if not self.Subscription:
            return "Plan"
        else:
            return self.Subscription.name

    @property
    def display_sub_subtitle(self):
        if not self.Subscription:
            return "Plan Description"
        else:
            return self.Subscription.subtitle

    @property
    def display_features_list(self):
        if not self.Subscription:
            return []
        else:
            return self.Subscription.get_features_as_list()

    @property
    def stripe_currency(self):
        return "gbp"

    @property
    def stripe_price(self):
        """Need to remove decimals"""
        return int(self.price * 100)

    def save(self, *args, **kwargs):
        if not self.stripe_id:
            stripe_id = helpers.billing.create_price(
                currency=self.stripe_currency,
                unit_amount=self.stripe_price,
                recurring=self.interval,
                product=self.product_stripe_id,
                metadata={
                    "subscription_plan_price_id": self.id,
                },
                raw=False,
            )
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)
        if self.featured and self.Subscription:
            qs = SubscriptionPrice.objects.filter(
                Subscription=self.Subscription, interval=self.interval
            ).exclude(id=self.id)
            qs.update(featured=False)


class SubscriptionStatus(models.TextChoices):
    """
    From stripe: Possible values are incomplete, incomplete_expired, trialing, active, past_due, canceled, unpaid, or paused.
    """

    ACTIVE = "active", "Active"
    TRIALING = "trialing", "Trialing"
    INCOMPLETE = "incomplete", "Incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired", "Incomplete Expired"
    PAST_DUE = "past_due", "Past Due"
    CANCELED = "canceled", "Cancelled"
    UNPAID = "unpaid", "Unpaid"
    PAUSED = "paused", "Paused"

class UserSubscriptionQuerySet(models.QuerySet):
    def by_user_ids(self, user_ids=None):
        qs=self
        if isinstance(user_ids, list):
            qs=self.filter(user_id__in=user_ids)
        elif isinstance(user_ids, int):
            qs=self.filter(user_id__in=[user_ids])
        elif isinstance(user_ids, str):
            qs=self.filter(user_id__in=[user_ids])
        return qs
    def by_active_trialling(self):
        active_qs_lookup = (
            Q(status = SubscriptionStatus.ACTIVE) |
            Q(status=SubscriptionStatus.TRIALING))
        self.filter(active_qs_lookup)
        return self

class UserSubscriptionManager(models.Manager):
    def get_queryset(self):
        return UserSubscriptionQuerySet(self.model, self._db)

    def by_user_ids(self, user_ids=None):
        return self.get_queryset().by_user_ids(user_ids=user_ids)


class UserSubscription(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True
    )
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    active = models.BooleanField(default=True)
    user_cancelled = models.BooleanField(default=False)
    original_period_start = models.DateTimeField(
        auto_now=False, auto_now_add=False, blank=True, null=True
    )
    current_period_start = models.DateTimeField(
        auto_now=False, auto_now_add=False, blank=True, null=True
    )
    current_period_end = models.DateTimeField(
        auto_now=False, auto_now_add=False, blank=True, null=True
    )
    status = models.CharField(
        max_length=20, null=True, blank=True, choices=SubscriptionStatus.choices
    )
    cancel_at_period_end = models.BooleanField(default=False)

    objects = UserSubscriptionManager()
    # @property
    # def billing_cycle_anchor(self):
    #     """
    #     https://docs.stripe.com/payments/checkout/billing-cycle
    #     Optional delay to start new subscription in
    #     Stripe checkout
    #     """
    #     if not self.current_period_end:
    #         return None
    #     return int(self.current_period_end.timestamp())

    def get_absolute_url(self):
        return reverse("user_subscription")

    def get_cancel_url(self):
        return reverse("user_subscription_cancel")

    @property
    def plan_name(self):
        if not self.subscription:
            return None
        return self.subscription.name

    @property
    def is_active(self):
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]

    def serialise(self):
        return {
            "plan_name": self.plan_name,
            "current_period_start": self.current_period_start,
            "current_period_end": self.current_period_end,
            "status": self.status,
        }

    def save(self, *args, **kwargs):
        if not self.original_period_start and self.current_period_start is not None:
            self.original_period_start = self.current_period_start

        super().save(*args, **kwargs)


def user_sub_post_save(sender, instance, *args, **kwargs):
    user_sub_instance = instance
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    groups_ids = []
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        groups_ids = groups.values_list("id", flat=True)
    if not ALLOW_CUSTOM_GROUPS:
        user.groups.set(groups_ids)
    else:
        sub_qs = Subscription.objects.filter(active=True)
        if subscription_obj is not None:
            sub_qs = sub_qs.exclude(id=subscription_obj.id)
        sub_groups = sub_qs.values_list("groups__id", flat=True)
        sub_groups_set = set(sub_groups)
        # groups_ids = groups.values_list('id', flat=True)
        current_groups = user.groups.all().values_list("id", flat=True)
        group_ids_set, current_groups_set = (
            set(groups_ids),
            set(current_groups) - sub_groups_set,
        )
        final_groups_ids = list(group_ids_set | current_groups_set)
        user.groups.set(final_groups_ids)


post_save.connect(user_sub_post_save, sender=UserSubscription)
