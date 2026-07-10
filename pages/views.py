import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .models import SitePage, SiteSetting

logger = logging.getLogger(__name__)


def page_detail(request, slug):
    page = get_object_or_404(SitePage, slug=slug, is_published=True)
    return render(request, "pages/page.html", {"page": page})


@require_http_methods(["GET", "POST"])
def contact(request):
    sent = False
    error = ""
    values = {"name": "", "phone": "", "email": "", "message": ""}

    if request.method == "POST":
        values = {
            "name": request.POST.get("name", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "message": request.POST.get("message", "").strip(),
        }
        if not (values["name"] and values["phone"] and values["message"]):
            error = "Please fill in your name, phone and message."
        else:
            body = (
                f"New message from the Safa Style contact form\n"
                f"------------------------------------------------\n"
                f"Name:  {values['name']}\n"
                f"Phone: {values['phone']}\n"
                f"Email: {values['email'] or '—'}\n\n"
                f"{values['message']}\n"
            )
            msg = EmailMessage(
                subject=f"Contact form — {values['name']}",
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_EMAIL],
                reply_to=[values["email"]] if values["email"] else None,
            )
            try:
                msg.send(fail_silently=False)
                sent = True
                values = {"name": "", "phone": "", "email": "", "message": ""}
            except Exception:
                logger.exception("Contact form email failed")
                error = (
                    "Sorry, your message couldn't be sent right now. "
                    "Please call or WhatsApp us instead."
                )

    return render(
        request,
        "pages/contact.html",
        {"sent": sent, "error": error, "values": values, "site": SiteSetting.load()},
    )


def find_us(request):
    return render(request, "pages/find_us.html", {"site": SiteSetting.load()})
