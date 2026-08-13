from django.core.management.base import BaseCommand, CommandError

from orders.emails import send_order_emails
from orders.models import Order


class Command(BaseCommand):
    help = "Resend customer + store emails for one or more order numbers."

    def add_arguments(self, parser):
        parser.add_argument(
            "order_numbers",
            nargs="+",
            help="Order number(s), e.g. SS26081379240",
        )

    def handle(self, *args, **options):
        for number in options["order_numbers"]:
            try:
                order = Order.objects.get(order_number=number)
            except Order.DoesNotExist as exc:
                raise CommandError(f"Order not found: {number}") from exc
            send_order_emails(order)
            self.stdout.write(self.style.SUCCESS(f"Triggered emails for {number}"))
