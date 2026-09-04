from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt, os, pika, json, threading, time

app = FastAPI(title="Order Service")
security = HTTPBearer()
SECRET = os.getenv("JWT_SECRET", "supersecretkey123")
RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://admin:admin123@localhost:5672/")

orders_db = []
processed_orders = []

def verify_token(creds: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(creds.credentials, SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_rabbit_channel():
    params = pika.URLParameters(RABBIT_URL)
    conn = pika.BlockingConnection(params)
    channel = conn.channel()
    channel.queue_declare(queue='order_queue', durable=True)
    return conn, channel

def consumer_worker():
    # Simulate async processing without DB locks
    while True:
        try:
            conn, channel = get_rabbit_channel()
            def callback(ch, method, properties, body):
                order = json.loads(body)
                print(f"[Consumer] Processing order {order}")
                time.sleep(1)  # Simulate heavy transaction
                processed_orders.append(order)
                orders_db.append(order)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='order_queue', on_message_callback=callback)
            print("[Consumer] Started listening...")
            channel.start_consuming()
        except Exception as e:
            print(f"Consumer error {e}, retrying in 5s")
            time.sleep(5)

@app.on_event("startup")
def start_consumer():
    t = threading.Thread(target=consumer_worker, daemon=True)
    t.start()

@app.post("/orders")
def place_order(product_id: int, quantity: int, background_tasks: BackgroundTasks, user=Depends(verify_token)):
    # Instead of direct DB write with lock, push to broker
    order = {
        "user": user["sub"],
        "role": user["role"],
        "product_id": product_id,
        "quantity": quantity,
        "status": "queued"
    }
    try:
        conn, channel = get_rabbit_channel()
        channel.basic_publish(
            exchange='',
            routing_key='order_queue',
            body=json.dumps(order),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Broker error: {e}")
    return {"message": "Order queued successfully - no DB lock used", "order": order}

@app.get("/orders")
def list_orders(user=Depends(verify_token)):
    # USER can see own, ADMIN sees all
    if user["role"] == "ADMIN":
        return {"orders": orders_db, "processed_count": len(processed_orders)}
    else:
        my = [o for o in orders_db if o["user"] == user["sub"]]
        return {"orders": my}

@app.get("/health")
def health():
    return {"status": "order-service OK", "queued": len(orders_db)}
