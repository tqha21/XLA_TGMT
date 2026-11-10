from celery import Celery, Task
from flask import Flask

def celery_init_app(app: Flask) -> Celery:
    """
    Initializes and configures Celery instance integrated with Flask App Context.
    Ensures tasks execute within the application context.
    """
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config.get("CELERY", {}))
    celery_app.set_default()
    
    # Auto-discover tasks in app.tasks
    celery_app.autodiscover_tasks(["app.tasks.image_tasks"])
    
    app.extensions["celery"] = celery_app
    return celery_app
