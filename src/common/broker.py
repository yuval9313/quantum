from faststream.redis import RedisBroker

broker = RedisBroker(url="redis://localhost:6379")

@broker.publisher("tasks")
def create_new_task():
    pass


@broker.subscriber("tasks")
def subscribe_to_task():
    pass
