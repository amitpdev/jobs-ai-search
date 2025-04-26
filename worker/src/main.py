from src.celery import celeryapp
from src.tasks.scrape import start as scrape_start


@celeryapp.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Register periodic tasks"""

    # Scraper
    sender.add_periodic_task(10.0 * 1, scrape_start.s(), name="add every 5m")
