from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from inference.core.env import METRICS_INTERVAL
from inference.core.version import __version__
from inference.enterprise.device_manager.command_handler import (
    Command,
    handle_command,
)
from inference.enterprise.device_manager.metrics_service import (
    send_metrics,
    send_latest_inferences,
)

app = FastAPI(
    title="Roboflow Device Manager",
    description="The device manager enables remote control and monitoring of Roboflow inference server containers",
    version=__version__,
    terms_of_service="https://roboflow.com/terms",
    contact={
        "name": "Roboflow Inc.",
        "url": "https://roboflow.com/contact",
        "email": "help@roboflow.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    root_path="/",
)


@app.get("/")
def root():
    return {
        "name": "Roboflow Device Manager",
        "version": __version__,
        "terms_of_service": "https://roboflow.com/terms",
        "contact": {
            "name": "Roboflow Inc.",
            "url": "https://roboflow.com/contact",
            "email": "help@roboflow.com",
        },
        "license_info": {
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
    }


@app.post("/exec_command")
async def exec_command(command: Command):
    handle_command(command.dict())
    return {"status": "ok"}


scheduler = BackgroundScheduler(job_defaults={"coalesce": True})
scheduler.add_job(send_metrics, "interval", seconds=METRICS_INTERVAL)
scheduler.add_job(send_latest_inferences, "interval", seconds=5)
scheduler.start()
