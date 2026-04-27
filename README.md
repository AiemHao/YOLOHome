# YOLOHome

Hệ thống giám sát và điều khiển nhà thông minh gồm:

- Website: Frontend + Backend API
- Gateway: Cầu nối MQTT <-> Serial để giao tiếp với kit
- MQTT Broker và MongoDB

## Cấu trúc thư mục

```text
YOLOHome/
├─ docker-compose.yml
├─ mosquitto/
│  └─ mosquitto.conf
├─ YOLOHome-Gateway/
│  ├─ Dockerfile
│  ├─ config.docker.yml
│  └─ GateWay/run.py
└─ YOLOHome-Website/
	├─ backend/
	│  └─ Dockerfile
	└─ frontend/
		└─ Dockerfile
```
## Tổng quan Docker Compose

File compose chính là docker-compose.yml ở thư mục root.

Các service đang chạy:

- mqtt: Mosquitto broker, cổng 1883
- mongo: MongoDB, cổng 27017
- backend: Node.js API, cổng 5000
- frontend: Nginx serve frontend, cổng 8080
- gateway: Python MQTT <-> Serial bridge

Luồng chính:

- frontend -> backend (HTTP)
- backend <-> mongo
- backend <-> mqtt
- gateway <-> mqtt
- gateway <-> serial device

## Cài đặt và chạy bằng Docker

### Chạy docker

Chạy hệ thống:

```powershell
docker compose up -d --build
# Để dừng và xóa các container nhưng vẫn giữ lại dữ liệu DB
docker compose stop

# Để xóa sạch hệ thống (bao gồm cả dữ liệu DB)
docker compose down -v
```

## Cấu hình Serial cho Gateway

Trong docker-compose.yml, service gateway đang map:

- COM15:COM15

Quy ước:

- Chỉ cần đổi COM bên trái theo máy 
- Giữ COM15 bên phải để khớp với YOLOHome-Gateway/config.docker.yml

Ví dụ nếu máy dùng COM7 thì sửa thành:

- COM7:COM15

## Cổng dịch vụ mặc định

- Frontend: http://localhost:8080
- Backend API: http://localhost:5000
- MQTT Broker: localhost:1883
- MongoDB: localhost:27017

