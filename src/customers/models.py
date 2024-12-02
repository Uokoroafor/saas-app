from django.conf import settings
from django.db import models
import helpers.billing

from allauth.account.signals import (
    user_signed_up as all_auth_user_signed_up,
    email_confirmed as all_auth_email_confirmed,
)

User = settings.AUTH_USER_MODEL  # auth.user


# Create your models here.
class Customer(models.Model):
    """
    Represents a customer linked to a user, with Stripe integration for billing.

    This model tracks the customer's Stripe ID, initial email used for registration,
    and whether that email has been confirmed.

    Attributes:
        user (User): A one-to-one relationship with the `User` model.
        stripe_id (Optional[str]): The Stripe customer ID associated with the user.
        init_email (Optional[str]): The initial email provided during user signup.
        init_email_confirmed (bool): Indicates if the initial email has been confirmed.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    init_email = models.EmailField(blank=True, null=True)
    init_email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}"

    def save(self, *args, **kwargs):
        """
        Overrides the save method to create a Stripe customer if necessary.

        If `stripe_id` is not set and the initial email is confirmed, a Stripe customer
        is created using the `billing.create_customer` helper, with the user's email and metadata.

        Args:
            *args (Any): Additional positional arguments passed to the save method.
            **kwargs (Any): Additional keyword arguments passed to the save method.
        """
        if not self.stripe_id:
            if self.init_email_confirmed and self.init_email:
                email = self.user.email
                if email != "" or email is not None:
                    stripe_id = helpers.billing.create_customer(
                        email=email,
                        raw=False,
                        metadata={
                            "user_id": self.user.id,
                            "username": self.user.username,
                        },
                    )
                    self.stripe_id = stripe_id
        super().save(*args, **kwargs)

    def all_auth_user_signed_up_handler(request, user, *args, **kwargs):
        """
        Signal handler for when a user signs up via allauth.

        Creates a new `Customer` instance linked to the user with the initial email set
        but not confirmed.

        Args:
            request (Any): The HTTP request object.
            user (User): The newly signed-up user.
            *args (Any): Additional positional arguments.
            **kwargs (Any): Additional keyword arguments.
        """
        email = user.email
        Customer.objects.create(
            user=user,
            init_email=email,
            init_email_confirmed=False,
        )

    all_auth_user_signed_up.connect(all_auth_user_signed_up_handler)

    def all_auth_email_confirmed_handler(
        request, email_address, *args, **kwargs
    ):
        """
        Signal handler for when an email address is confirmed via allauth.

        Updates the `init_email_confirmed` field for any matching `Customer` objects
        where the initial email matches the confirmed email address.

        Args:
            request (Any): The HTTP request object.
            email_address (str): The email address that was confirmed.
            *args (Any): Additional positional arguments.
            **kwargs (Any): Additional keyword arguments.
        """
        qs = Customer.objects.filter(
            init_email=email_address,
            init_email_confirmed=False,
        )

        for obj in qs:
            obj.init_email_confirmed = True
            obj.save()
        # Could also use qs update here but it won't complete the corresponding stripe step FYI
        # Note: Using `update()` would not trigger the save logic for Stripe updates.

    all_auth_email_confirmed.connect(all_auth_email_confirmed_handler)
