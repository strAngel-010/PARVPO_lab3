from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import aio_pika
import json
import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

RABBIT_REPLY = "amq.rabbitmq.reply-to"
RABBIT_ADDRESS = "amqp://guest:guest@rabbitmq/"

app = FastAPI()

max_processing_time = 0.0

@app.middleware("http")
async def log_request_response_time(request: Request, call_next):
    global max_processing_time
    start_time = time.time()
    response = await call_next(request)
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000 
    if duration_ms > max_processing_time:
        max_processing_time = duration_ms
    return response

@app.get("/log")
async def get_logging_info():
    global max_processing_time
    print(f"Max processing time: {max_processing_time:.2f}ms", flush=True)
    max_processing_time = 0.0
    return JSONResponse(status_code=200, content={})


@app.post("/orders")
async def create_order(order: dict):
    connection = await aio_pika.connect_robust(RABBIT_ADDRESS)
    order["status"] = "received"
    order_json = json.dumps(order)
    response_data = None

    async with connection:
        
        channel = await connection.channel()

        callback_queue = await channel.get_queue(RABBIT_REPLY)
        rq = asyncio.Queue(maxsize=1)

        consumer_tag = await callback_queue.consume(
            callback=rq.put,
            no_ack=True,
        )

        await channel.default_exchange.publish(
            message=aio_pika.Message(
                body=order_json.encode('utf-8'),
                reply_to=RABBIT_REPLY
            ),
            routing_key="orders"
        )

        response = await rq.get()
        response_json = response.body.decode('utf-8')
        response_data = json.loads(response_json)
        print(response_data, flush=True)
        await callback_queue.cancel(consumer_tag)
        await connection.close()
    return response_data

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    print(order_id, flush=True)
    connection = await aio_pika.connect_robust(RABBIT_ADDRESS)
    order_id_json = json.dumps({"order_id": order_id})
    
    status_data = None
    async with connection:
        channel = await connection.channel()

        callback_queue = await channel.get_queue(RABBIT_REPLY)
        rq = asyncio.Queue(maxsize=1)

        consumer_tag = await callback_queue.consume(
            callback=rq.put,
            no_ack=True
        )

        await channel.default_exchange.publish(
            message=aio_pika.Message(
                body=order_id_json.encode('utf-8'),
                reply_to=RABBIT_REPLY
            ),
            routing_key="status"
        )

        response = await rq.get()
        response_json = response.body.decode('utf-8')
        status_data = json.loads(response_json)
        print(status_data, flush=True)
        await callback_queue.cancel(consumer_tag)
        await connection.close()
        if status_data is not None: return status_data
        else: raise HTTPException(status_code=404, detail="Order not found")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": str(exc)})

print("Started API")
