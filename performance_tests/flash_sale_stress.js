import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = 'http://web:8000';

export let options = {
  stages: [
    { duration: '10s', target: 100 },
    { duration: '30s', target: 1000 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {

    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

export function setup() {
  console.log('Iniciando Setup del Test');


  const loginRes = http.post(`${BASE_URL}/users/token`, {
    username: 'SuperUser',
    password: 'Test12345$' // pragma: allowlist secret
  });

  check(loginRes, { 'Login exitoso': (r) => r.status === 200 });
  const token = loginRes.json('access_token');

  const prodPayload = JSON.stringify({
    name: `Zapatillas-Flash-Sale-${Date.now()}`,
    category: "LoadTest",
    price: 199.99,
    stock: 1000000,
    description: "Producto generado por k6",
    available: true
  });

  const prodRes = http.post(`${BASE_URL}/products/create_product`, prodPayload, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  });

  check(prodRes, { 'Producto creado': (r) => r.status === 201 });
  const productId = prodRes.json('id');

  console.log(`Setup Completo. Producto ID: ${productId}`);

  return { token: token, productId: productId };
}

export default function (data) {
  const payload = JSON.stringify({
    items: [{ product_id: data.productId, quantity: 1 }]
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${data.token}`
    }
  };

  let res = http.post(`${BASE_URL}/orders/`, payload, params);

  check(res, { 'Orden procesada (201)': (r) => r.status === 201 });

  sleep(0.1);
}
