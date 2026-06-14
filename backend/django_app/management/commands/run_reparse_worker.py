import time
from django.core.management.base import BaseCommand
from backend.django_app.models import ReparseJob
from backend.django_app.reparse_job import process_reparse_job


class Command(BaseCommand):
    help = "Run a simple ReparseJob worker that processes queued jobs."

    def handle(self, *args, **options):
        self.stdout.write("Starting reparse worker (CTRL+C to stop)")
        try:
            while True:
                job = ReparseJob.objects.filter(status="queued").order_by("created_at").first()
                if job:
                    self.stdout.write(f"Processing job {job.id} kind={job.kind}")
                    job.status = "running"
                    job.progress = 0
                    job.save()
                    try:
                        process_reparse_job(job)
                        self.stdout.write(f"Job {job.id} done")
                    except Exception as e:
                        job.status = "failed"
                        job.error = str(e)
                        job.save()
                        self.stdout.write(f"Job {job.id} failed: {e}")
                else:
                    time.sleep(3)
        except KeyboardInterrupt:
            self.stdout.write("Worker stopping")
