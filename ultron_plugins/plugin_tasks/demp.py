from ultron.tasks import celery_app
from ultron import objects

@celery_app.task
def testfunc(clientname, adminname, reportname, **kwargs):
    """
    Just a demo task
    """
    client = objects.Client(clientname, adminname, reportname)
    client.state.update({'test': 'SUCCESS'})
    client.save()
    print(client.__dict__)
    print(kwargs)
    return {'conclusion': 'Test is successful', 'kwargs': kwargs}
