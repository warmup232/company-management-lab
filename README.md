# company-management-lab
# Inventory Management REST API

소규모 매장 및 사업자를 위한 재고 관리 REST API입니다.

## Tech Stack

- Python
- Flask
- MySQL
- REST API
- Linux

## Features

- 상품 등록
- 상품 조회
- 상품 수정
- 상품 삭제
- 재고 입고
- 재고 출고
- 재고 부족 조회
- 입출고 기록 저장

## API

### Health Check

GET /health

### Products

GET /products

GET /products/{id}

POST /products

PUT /products/{id}

DELETE /products/{id}

### Stock

POST /products/{id}/stock/in

POST /products/{id}/stock/out

### Low Stock

GET /products/low-stock?threshold=10

## Installation

Create virtual environment:

python3 -m venv .venv

Activate:

source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Run:

python app.py
