
### using select_for_update *****
from django.core.management.base import BaseCommand
from email_config.models import EmailSend, SMSSend, PushSend
from administrations.utils import send_generic_mail, send_generic_sms, send_generic_push
from concurrent.futures import ThreadPoolExecutor
from django.db.models import Q
from django.db import transaction

class Command(BaseCommand):
    help = 'Send notifications safely without duplicate (no model change)'

    type_map = {
        0: [EmailSend, send_generic_mail, 'to_email'],
        1: [SMSSend, send_generic_sms, 'to_number'],
        2: [PushSend, send_generic_push, None],
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '-t', '--type',
            default=1,
            type=int,
            choices=self.type_map.keys(),
        )

    def handle(self, *args, **options):
        notify_type = options['type']

        if notify_type not in self.type_map:
            self.stdout.write(self.style.ERROR(f"Invalid Type: {notify_type}"))
            return

        Model, send_function, field = self.type_map[notify_type]

        base_query = Q(is_sent=False) & \
                     Q(template__is_active_trigger=True) & \
                     Q(tried_count__lt=3)

        if field:
            base_query &= ~(Q(**{f"{field}__isnull": True}) | Q(**{field: ''}))

        # 🔒 STEP 1: Lock rows (no duplicate pick)
        with transaction.atomic():
            queryset = (
                Model.objects
                .select_for_update(skip_locked=True)
                .filter(base_query)
                .order_by('id')[:50]   # batch limit
            )

            instances = list(queryset)

        if not instances:
            self.stdout.write("No pending notifications")
            return

        # 🚀 STEP 2: Send outside transaction
        resp = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(send_function, instance=instance): instance
                for instance in instances
            }

            for future in futures:
                instance = futures[future]
                try:
                    result = future.result()

                    if result:
                        instance.is_sent = True
                        resp.append(instance.id)

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error ID {instance.id}: {e}"))

                finally:
                    instance.tried_count += 1
                    instance.save(update_fields=['is_sent', 'tried_count'])

        self.stdout.write(
            self.style.SUCCESS(f"{notify_type} sent IDs --> {resp}")
        )
