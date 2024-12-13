from typing import Any, Dict, List, Optional, Union
from django.db import models
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.db.models.signals import post_save
from django.conf import settings
import helpers.billing
import helpers.currency_utils
from django.urls import reverse
from django.utils import timezone
import datetime

User = settings.AUTH_USER_MODEL  # auth.User

ALLOW_CUSTOM_GROUPS = True
SUBSCRIPTION_PERMISSIONS = [
    ("advanced", "Advanced Permissions"),  # subscriptions.advanced
    ("pro", "Pro Permissions"),  # subscriptions.pro
    ("basic", "Basic Permissions"),  # subscriptions.basic
    ("basic_ai", "Basic AI Permissions"),  # subscriptions.basic
]


class Subscription(models.Model):
    """Model representing a Stripe subscription product.

    This model defines a subscription plan with associated features,
    groups, permissions, and Stripe integration. It also supports ordering,
    activation status, and featured status for display on the Django Pricing page.
    """

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
    order = models.IntegerField(
        default=-1, help_text="Order on Django Pricing Page"
    )
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

    def __str__(self) -> str:
        """Returns a string representation of the subscription's name."""
        return f"{self.name}"

    class Meta:
        """Meta options for the `Subscription` model.

        - Sets custom permissions for the model using `SUBSCRIPTION_PERMISSIONS`.
        - Specifies the default ordering of `Subscription` instances by:
          1. `order` (ascending)
          2. `featured` (ascending, featured items first)
          3. `updated` (descending, most recently updated first)
        """

        permissions = SUBSCRIPTION_PERMISSIONS
        ordering = ["order", "featured", "-updated"]

    def get_features_as_list(self) -> List[str]:
        """Converts the subscription's features text into a list of individual features.

        This method splits the `features` field by newline characters and returns a list
        of trimmed feature strings. It ensures that empty or whitespace-only features
        are excluded from the output.

        Returns:
            List[str]: A list of individual features as strings. Returns an empty list
            if no features are specified.
        """
        if not self.features:
            return []
        return [x.strip() for x in self.features.split("\n") if x.strip()]

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Overrides the save method to ensure a Stripe product is created if necessary.

        This method checks if the `stripe_id` field is empty. If so, it calls a billing
        helper to create a corresponding Stripe product using the subscription's `name`
        and `id`. The `stripe_id` is then set to the newly created Stripe product's ID
        before saving the model instance.

        Args:
            *args (Any): Positional arguments passed to the base `save` method.
            **kwargs (Any): Keyword arguments passed to the base `save` method.

        Returns:
            None: This method does not return a value.
        """
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
    """Model representing a Stripe price for a subscription product.

    This model links a price to a `Subscription` and includes details such as
    billing interval, price amount, display order, and whether it is featured
    on the Django Pricing Page. It also tracks timestamps for updates and creation.
    """

    class IntervalChoices(models.TextChoices):
        """Enum of billing interval choices for the subscription price.

        Attributes:
            MONTHLY: Represents a monthly billing cycle.
            YEARLY: Represents an annual billing cycle.
        """

        MONTHLY = "month", "Monthly"
        YEARLY = "year", "Annually"

    Subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The subscription product associated with this price.",
    )
    stripe_id = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        help_text="The Stripe ID for the price object.",
    )
    interval = models.CharField(
        max_length=120,
        default=IntervalChoices.MONTHLY,
        choices=IntervalChoices.choices,
        help_text="The billing interval for the subscription price.",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=9.99,
        help_text="The price amount in the specified currency.",
    )
    order = models.IntegerField(
        default=-1, help_text="Display order on the Django Pricing Page."
    )
    featured = models.BooleanField(
        default=True,
        help_text="Indicates if this price is featured on the Django Pricing Page.",
    )

    # Add Timestamps
    updated = models.DateTimeField(
        auto_now=True,
        help_text="The timestamp when the price was last updated.",
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="The timestamp when the price was created.",
    )

    class Meta:
        """Meta options for the `SubscriptionPrice` model.

        - Specifies the default ordering of `SubscriptionPrice` instances:
            1. By the `order` field of the associated `Subscription`.
            2. By `order` within the `Subscription`.
            3. By `featured` status (ascending).
            4. By `updated` timestamp (descending).
        """

        ordering = ["Subscription__order", "order", "featured", "-updated"]

    def get_checkout_url(self) -> str:
        """Generates the checkout URL for a subscription price.

        Returns:
            str: The URL for the checkout page, with the `price_id` as part of the URL.
        """
        return reverse("sub-price-checkout", kwargs={"price_id": self.id})

    @property
    def product_stripe_id(self) -> Optional[str]:
        """Returns the Stripe product ID associated with the subscription.

        This property retrieves the `stripe_id` of the associated `Subscription` object, if available.
        If the `Subscription` is not set, it returns `None`.

        Returns:
            Optional[str]: The Stripe ID of the subscription's product, or `None` if no associated
            subscription exists.
        """
        if not self.Subscription:
            return None
        else:
            return self.Subscription.stripe_id

    @property
    def display_sub_name(self) -> str:
        """Returns the name of the subscription plan for display.

        This property returns the name of the associated `Subscription` plan. If no `Subscription`
        is linked, it returns a default string "Plan".

        Returns:
            str: The name of the subscription plan, or "Plan" if no subscription is associated.
        """
        if not self.Subscription:
            return "Plan"
        else:
            return self.Subscription.name

    @property
    def display_sub_subtitle(self) -> str:
        """Returns the subtitle of the associated subscription plan.

        This property retrieves the `subtitle` of the associated `Subscription` plan. If no subscription
        is linked, it returns a default string "Plan Description".

        Returns:
            str: The subtitle of the subscription plan, or "Plan Description" if no subscription is associated.
        """
        if not self.Subscription:
            return "Plan Description"
        else:
            return self.Subscription.subtitle

    @property
    def display_features_list(self) -> list[Optional[str]]:
        """Returns a list of features for the associated subscription plan.

        This retrieves the list of features associated with the subscription, using the
        `get_features_as_list` method of the `Subscription` model. If no subscription is linked, it returns
        an empty list.

        Returns:
            list[Optional[str]]: A list of subscription features, or an empty list if no subscription is associated.
        """
        if not self.Subscription:
            return []
        else:
            return self.Subscription.get_features_as_list()

    @property
    def stripe_currency(self) -> str:
        """Returns the currency used for the subscription, falling back to the default from settings.

        This property returns the currency code for the subscription, either from a specific field
        or the global default in the settings.

        Returns:
            str: The currency code for the subscription, defaulting to settings.DEFAULT_CURRENCY.
        """
        return getattr(self, "currency", settings.DEFAULT_CURRENCY)

    @property
    def stripe_currency_symbol(self) -> str:
        """Returns the currency symbol used for the subscription.

        Returns:
            str: The currency symbol for the subscription will return unk if not known.
        """
        return helpers.currency_utils.get_currency_symbol(self.stripe_currency)

    @property
    def stripe_price(self) -> int:
        """
        Calculates and returns the Stripe price by converting the price (in local currency)
        to an integer representing cents, as Stripe requires amounts to be in the smallest
        currency unit (e.g., cents for USD, pence for GBP).

        Returns:
            int: The price in the smallest currency unit (e.g., cents or pence).
        """
        return int(self.price * 100)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Overrides the default save method to create a Stripe price object if one does not
        already exist for this instance. It also ensures that only one 'featured' price
        exists per subscription and interval.

        This method:
            - Creates a Stripe price object if `stripe_id` is not set.
            - Updates the 'featured' status of other prices for the same subscription and interval.

        Args:
            *args: Additional positional arguments passed to the parent save method.
            **kwargs: Additional keyword arguments passed to the parent save method.

        Returns:
            None: This method does not return anything; it just saves the object.
        """
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
    Enum for subscription statuses in Stripe.

    This class defines possible values for subscription status as provided by Stripe. These statuses indicate the
    current state of a subscription and include options like 'active', 'trialing', 'incomplete', and more.

    Attributes:
        ACTIVE: The subscription is currently active.
        TRIALING: The subscription is in a trial period.
        INCOMPLETE: The subscription is incomplete due to some issue (e.g., payment failure).
        INCOMPLETE_EXPIRED: The subscription was incomplete and has expired without resolving.
        PAST_DUE: The subscription payment is overdue.
        CANCELED: The subscription has been canceled.
        UNPAID: The subscription is unpaid due to a billing issue.
        PAUSED: The subscription is paused and temporarily inactive.
    """

    ACTIVE = "active", "Active"
    TRIALING = "trialing", "Trialling"
    INCOMPLETE = "incomplete", "Incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired", "Incomplete Expired"
    PAST_DUE = "past_due", "Past Due"
    CANCELED = "canceled", "Cancelled"
    UNPAID = "unpaid", "Unpaid"
    PAUSED = "paused", "Paused"


class UserSubscriptionQuerySet(models.QuerySet):
    """
    Custom QuerySet for filtering user subscriptions.

    Provides utility methods to filter user subscriptions based on user IDs or subscription statuses
    such as 'active' or 'trialing'.
    """

    def by_user_ids(
        self, user_ids: Optional[Union[List[Union[int, str]], int, str]] = None
    ) -> models.QuerySet:
        """
        Filters the queryset by a list of user IDs or a single user ID.

        Args:
            user_ids (Optional[Union[List[Union[int, str]], int, str]]):
                A list of user IDs, a single integer user ID, or a string user ID.

        Returns:
            models.QuerySet: A queryset filtered by the provided user IDs.
        """
        qs = self
        if isinstance(user_ids, list):
            qs = self.filter(user_id__in=user_ids)
        elif isinstance(user_ids, int):
            qs = self.filter(user_id__in=[user_ids])
        elif isinstance(user_ids, str):
            qs = self.filter(user_id__in=[user_ids])
        return qs

    def by_active_trialling(self) -> models.QuerySet:
        """
        Filters the queryset for active or trialing subscriptions.

        Returns:
            models.QuerySet: A queryset filtered by active or trialing subscription statuses.
        """
        active_qs_lookup = Q(status=SubscriptionStatus.ACTIVE) | Q(
            status=SubscriptionStatus.TRIALING
        )
        qs = self.filter(active_qs_lookup)
        return qs

    def by_days_remaining(self, days_remaining: int = 7) -> models.QuerySet:
        """
        Filters subscriptions that end within a specified number of days from now.

        Args:
            days_remaining (int): The number of days from now to filter subscriptions
                                  (default is 7).

        Returns:
            models.QuerySet: A queryset filtered to include subscriptions whose
                             `current_period_end` falls on the specified day.
        """
        now = timezone.now()
        in_n_days = now + datetime.timedelta(days=days_remaining)
        start_of_day = in_n_days.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_of_day = in_n_days.replace(
            hour=23, minute=59, second=59, microsecond=999_999
        )
        qs = self.filter(
            current_period_end__gte=start_of_day,
            current_period_end__lte=end_of_day,
        )
        return qs

    def by_days_since(self, days_since: int = 7) -> models.QuerySet:
        """
        Filters subscriptions that ended a specified number of days ago.

        Args:
            days_since (int): The number of days ago to filter subscriptions
                              (default is 7).

        Returns:
            models.QuerySet: A queryset filtered to include subscriptions whose
                             `current_period_end` falls on the specified past day.
        """
        now = timezone.now()
        for_n_days = now - datetime.timedelta(days=days_since)
        start_of_day = for_n_days.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_of_day = for_n_days.replace(
            hour=23, minute=59, second=59, microsecond=999_999
        )
        qs = self.filter(
            current_period_end__gte=start_of_day,
            current_period_end__lte=end_of_day,
        )
        return qs

    def by_days_range(self, from_days: int, to_days: int) -> models.QuerySet:
        """
        Filters subscriptions whose end dates fall within a specified range of days.

        Args:
            from_days (int): The starting point in days from now for filtering.
            to_days (int): The ending point in days from now for filtering.

        Returns:
            models.QuerySet: A queryset filtered to include subscriptions whose
                             `current_period_end` falls within the specified range.
        """
        now = timezone.now()
        from_days_from_now = now + datetime.timedelta(days=from_days)
        to_days_from_now = now + datetime.timedelta(days=to_days)
        start_date = from_days_from_now.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = to_days_from_now.replace(
            hour=23, minute=59, second=59, microsecond=999_999
        )
        qs = self.filter(
            current_period_end__gte=start_date,
            current_period_end__lte=end_date,
        )
        return qs


class UserSubscriptionManager(models.Manager):
    """
    Custom manager for user subscriptions.

    Provides access to the custom QuerySet methods defined in `UserSubscriptionQuerySet`.
    """

    def get_queryset(self) -> UserSubscriptionQuerySet:
        """
        Returns the custom queryset for user subscriptions.

        Overrides the default `get_queryset` method to return an instance of
        `UserSubscriptionQuerySet`, enabling the use of custom filtering methods.

        Returns:
            UserSubscriptionQuerySet: A custom queryset for user subscriptions.
        """
        return UserSubscriptionQuerySet(self.model, self._db)

    def by_user_ids(
        self, user_ids: Optional[Union[List[Union[int, str]], int, str]] = None
    ) -> models.QuerySet:
        """
        Filters subscriptions by user IDs using the custom QuerySet method.

        Args:
            user_ids (Optional[Union[List[Union[int, str]], int, str]]):
                A list of user IDs, a single integer user ID, or a string user ID.

        Returns:
            models.QuerySet: A queryset filtered by the provided user IDs.
        """
        return self.get_queryset().by_user_ids(user_ids=user_ids)


class UserSubscription(models.Model):
    """
    Represents a user's subscription details.

    This model stores information about a user's subscription status, including the subscription's
    Stripe ID, active status, and various timestamps related to the subscription period.

    Attributes:
        user (User): A one-to-one relationship with the `User` model.
        subscription (Subscription): A foreign key to the `Subscription` model. It can be null or blank.
        stripe_id (Optional[str]): The Stripe ID associated with the user's subscription.
        active (bool): Indicates whether the subscription is currently active. Defaults to `True`.
        user_cancelled (bool): Indicates if the user has canceled the subscription. Defaults to `False`.
        original_period_start (Optional[datetime]): The start date of the original subscription period.
        current_period_start (Optional[datetime]): The start date of the current subscription period.
        current_period_end (Optional[datetime]): The end date of the current subscription period.
        status (Optional[str]): The current status of the subscription. Choices are defined by `SubscriptionStatus`.
        cancel_at_period_end (bool): Indicates if the subscription will cancel at the end of the current period.

    Managers:
        objects (UserSubscriptionManager): Custom manager providing additional query methods.
    """

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
        max_length=20,
        null=True,
        blank=True,
        choices=SubscriptionStatus.choices,
    )
    cancel_at_period_end = models.BooleanField(default=False)

    objects = UserSubscriptionManager()

    @property
    def billing_cycle_anchor(self):
        """
        Returns the billing cycle anchor timestamp for the subscription.

        The billing cycle anchor is the time at which the current billing cycle ends.
        If `current_period_end` is not set, it returns `None`. Otherwise, it returns
        the Unix timestamp of `current_period_end`.

        Returns:
            Optional[int]: The Unix timestamp representing the billing cycle anchor,
                           or `None` if `current_period_end` is not set.
        """
        if not self.current_period_end:
            return None
        return int(self.current_period_end.timestamp())

    def get_absolute_url(self) -> str:
        """
        Returns the absolute URL for the user subscription detail view.

        Useful for redirecting users to their subscription management page.

        Returns:
            str: The URL for the user subscription view.
        """
        return reverse("user_subscription")

    def get_cancel_url(self) -> str:
        """
        Returns the URL to cancel the user subscription.

        This URL is typically used to allow users to cancel their subscriptions via a frontend interface.

        Returns:
            str: The URL for canceling the user subscription.
        """
        return reverse("user_subscription_cancel")

    @property
    def plan_name(self) -> Optional[str]:
        """
        Returns the name of the current subscription plan.

        This is used for display purposes in the frontend. If no subscription exists, it returns `None`.

        Returns:
            Optional[str]: The name of the current subscription plan, or `None` if no subscription exists.
        """
        if not self.subscription:
            return None
        return self.subscription.name

    @property
    def is_active(self) -> bool:
        """
        Checks if the subscription is active or trialing.

        This property determines if the subscription is currently in an active state
        or in a trial period.

        Returns:
            bool: `True` if the subscription is active or trialing, otherwise `False`.
        """
        return self.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        ]

    def serialise(self) -> Dict[str, str | int | bool]:
        """
        Serialises the subscription details into a dictionary.

        Provides a simplified representation of the subscription for use in APIs
        or other serialisation needs.

        Returns:
            Dict[str, Union[str, int, bool, Optional[str]]]: A dictionary containing:
                - `plan_name`: The name of the subscription plan.
                - `current_period_start`: The start of the current subscription period.
                - `current_period_end`: The end of the current subscription period.
                - `status`: The current subscription status.
        """
        return {
            "plan_name": self.plan_name,
            "current_period_start": self.current_period_start,
            "current_period_end": self.current_period_end,
            "status": self.status,
        }

    def save(self, *args: Any, **kwargs: Any):
        """
        Overrides the save method to ensure original period start is set.

        If `original_period_start` is not set but `current_period_start` exists,
        it sets `original_period_start` to `current_period_start` before saving.

        Args:
            *args (Any): Positional arguments passed to the `save` method.
            **kwargs (Any): Keyword arguments passed to the `save` method.
        """
        if (
            not self.original_period_start
            and self.current_period_start is not None
        ):
            self.original_period_start = self.current_period_start

        super().save(*args, **kwargs)


def user_sub_post_save(
    sender: type, instance: UserSubscription, *args: Any, **kwargs: Any
):
    """
    Synchronises the user's group memberships after a subscription is saved.

    This function updates the groups associated with a user based on the user's subscription.
    If `ALLOW_CUSTOM_GROUPS` is `False`, it sets the user's groups to match the groups associated
    with the subscription. If `ALLOW_CUSTOM_GROUPS` is `True`, it ensures the user retains custom
    groups while removing those from inactive subscriptions.

    Args:
        sender (type): The model class that triggered the signal (UserSubscription).
        instance (UserSubscription): The instance of the subscription being saved.
        *args (Any): Additional positional arguments passed by the signal.
        **kwargs (Any): Additional keyword arguments passed by the signal.

    Returns:
        None: The method does not return any value.
    """
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
