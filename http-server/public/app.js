document.getElementById('orderForm').addEventListener('submit', async (event) => {
    document.getElementById('responseMessage').textContent = "Заказ отправляется...";
    event.preventDefault();
    
    const customerName = document.getElementById('customerName').value;
    const product = document.getElementById('product').value;
    const address = document.getElementById('address').value;
    const quantity = parseInt(document.getElementById('quantity').value, 10);
    
    try {
        const orderPromises = Array.from({length: quantity}, (_, i) => {
            return fetch('/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    customer_name: customerName,
                    product: product,
                    address: address,
                }),
            }).then(response => {
                if (!response.ok) {
                    throw new Error(`Order failed: ${response.statusText}`);
                }
                return response
            });
        });      
        
        const results = await Promise.all(orderPromises);
        const last_response = results[results.length-1]
        if (last_response.ok) {
            const json_data = await last_response.json();
            const order_id = json_data.order_id;
            document.getElementById('responseMessage').textContent = 
                `Заказ ${order_id} успешно создан!`;
        } else {
            document.getElementById('responseMessage').textContent = 
                'Ошибка при отправке заказа.';
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('responseMessage').textContent = 'Сетевая ошибка.';
    }
});

document.getElementById('statusForm').addEventListener('submit', async (event) => {
    document.getElementById('statusResult').textContent = 'Поиск заказа...'
    event.preventDefault();
    
    const orderId = document.getElementById('orderId').value;
    
    try {
        const response = await fetch(`/orders/${orderId}`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById('statusResult').textContent = 
                `Статус заказа: ${data.status}`;
        } else {
            document.getElementById('statusResult').textContent = 
                'Заказ не найден.';
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('statusResult').textContent = 'Сетевая ошибка.';
    }
});
