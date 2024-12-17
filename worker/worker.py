import aio_pika
import psycopg2
import json
import random
import asyncio
from functools import partial

RABBITMQ_ADDRESS = "amqp://guest:guest@rabbitmq/"
db_conn = None
cursor = None

async def establish_db_connection():
    while True:
        try:
            db_conn = psycopg2.connect(
                dbname='orders_db',
                user='postgres',
                password='postgres',
                host='postgres',
                port="5432"
            )
            print("Connected to database", flush=True)
            return db_conn
        except Exception:
            print("Failed to connect to DB. Retrying in 3 s...", flush=True)
            await asyncio.sleep(3)

async def establish_rabbitmq_connection():
    connected = 0
    while not connected:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_ADDRESS)
            connected = 1
            print("Connected to RabbitMQ", flush=True)
            return connection
        except Exception:
            print("Failed to connect to RabbitMQ. Retrying in 3 s...", flush=True)
            await asyncio.sleep(3)


def update_order_status(order_id, status):
    cursor.execute(
        "UPDATE orders SET status = %s WHERE id = %s",
        (status, order_id)
    )
    db_conn.commit()

async def process_order(order_id):
    #print("Обработка заказа "+str(order_id)+" началась.", flush=True)
    await asyncio.sleep(random.randint(5, 10))
    update_order_status(order_id, 'processed')
    #print("Обработка заказа "+str(order_id)+" завершена.", flush=True)

def save_order_to_db(order: dict):
    cursor.execute(
        """INSERT INTO orders (customer_name, product, status, address) 
        VALUES (%s, %s, %s, %s)
        RETURNING ID""",
        (order["customer_name"], order["product"], 'pending', order["address"])
    )
    order_id = cursor.fetchone()[0]
    response_data = {"order_id": order_id}
    print(order_id)
    db_conn.commit()
    return response_data

def get_order_status(order_id):
    print("Getting status for order "+str(order_id), flush=True)
    cursor.execute(
        "SELECT status FROM orders WHERE id = %s", (order_id, )
    )
    fetch_result = cursor.fetchall()
    if fetch_result:
        status = fetch_result[0][0]
        response_data = {"status": status}
        print(status)
        db_conn.commit()
        return response_data
    else: return None

async def orders_consumer(
    msg: aio_pika.IncomingMessage,
    channel: aio_pika.RobustChannel,
):
    async with msg.process():
        print("orders_consumer recieved :"+str(msg.body), flush=True);
        order = json.loads(msg.body.decode('utf-8'))
        response_data = save_order_to_db(order)
        response_json = json.dumps(response_data)
        asyncio.create_task(process_order(response_data["order_id"]))

        if msg.reply_to:
            await channel.default_exchange.publish(
                message=aio_pika.Message(
                    body=response_json.encode('utf-8'),
                    correlation_id=msg.correlation_id,
                ),
                routing_key=msg.reply_to,
            )

async def status_consumer(
    msg: aio_pika.IncomingMessage,
    channel: aio_pika.RobustChannel,
):
    async with msg.process():
        print("status_consumer recieved :"+str(msg.body), flush=True);
        order_id = json.loads(msg.body.decode('utf-8'))
        response_data = get_order_status(order_id["order_id"])
        response_json = json.dumps(response_data)

        if msg.reply_to:
            await channel.default_exchange.publish(
                message=aio_pika.Message(
                    body=response_json.encode('utf-8'),
                    correlation_id=msg.correlation_id,
                ),
                routing_key=msg.reply_to,
            )
        

async def main():
    global db_conn, cursor
    db_conn = await establish_db_connection()
    cursor = db_conn.cursor()

    print("Starting async listeners...")
    listener2 = loop.create_task(orders_listener())
    listener3 = loop.create_task(status_listener())
    await asyncio.wait([listener2, listener3])

async def orders_listener():
    print("Starting orders listener", flush=True)
    connection = await establish_rabbitmq_connection()

    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("orders")
        await queue.consume(partial(orders_consumer, channel=channel))

        try:
            await asyncio.Future()
        except Exception:
            pass
        connection.close()

async def status_listener():
    print("Starting status listener", flush=True)
    connection = await aio_pika.connect_robust(RABBITMQ_ADDRESS)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("status")
        await queue.consume(partial(status_consumer, channel=channel))

        try:
            await asyncio.Future()
        except Exception:
            pass
        connection.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try: loop.run_until_complete(main())
    finally: loop.close()
