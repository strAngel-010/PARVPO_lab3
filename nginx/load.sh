URL="http://0.0.0.0:80/orders"
REQUESTS_PER_SECOND=$1

INTERVAL=$(echo "1 / $REQUESTS_PER_SECOND" | bc -l)

while true; do
  timeout 10s curl -X POST $URL \
       -H "Content-Type: application/json" \
       -d '{"customer_name": "name", "product": "product", "address": "address"}' >/dev/null 2>&1 &
  sleep $INTERVAL
done

wait
