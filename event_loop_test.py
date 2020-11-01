import asyncio
import time

# https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor
# https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
# Read about coroutines

async def say_after(delay, what):
    await asyncio.sleep(delay)
    print(what)

async def main():
    task1 = asyncio.create_task(
        say_after(1, 'hello')
    )
    task2 = asyncio.create_task(
        say_after(2, 'world')
    )

    print(f'Started at {time.strftime("%X")}')

    # Wait until both tasks are completed 
    await task1
    await task2

    print(f"finished at {time.strftime('%X')}")

asyncio.run(main())