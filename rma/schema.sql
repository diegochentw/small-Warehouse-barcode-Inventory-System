BEGIN TRANSACTION;
DROP TABLE IF EXISTS "user";
CREATE TABLE IF NOT EXISTS "user" (
	"user_id"	INTEGER,
	"username"	TEXT NOT NULL UNIQUE,
	"password"	TEXT NOT NULL,
	PRIMARY KEY("user_id" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "category";
CREATE TABLE IF NOT EXISTS "category" (
	"category_id"	INTEGER,
	"category_name"	TEXT NOT NULL,
	PRIMARY KEY("category_id" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "customer";
CREATE TABLE IF NOT EXISTS "customer" (
	"customer_id"	INTEGER,
	"customer_name"	TEXT NOT NULL,
	"contact"	TEXT,
	"type"	TEXT,
	"phone"	TEXT,
	"email"	TEXT,
	"address"	TEXT,
	"created_date"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	"notes"	TEXT,
	PRIMARY KEY("customer_id" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "shipment";
CREATE TABLE IF NOT EXISTS "shipment" (
	"shipment_id"	INTEGER,
	"type"	TEXT,
	"category_id"	INTEGER,
	"customer_id"	INTEGER,
	"note"	TEXT,
	"created_date"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("shipment_id" AUTOINCREMENT),
	FOREIGN KEY("customer_id") REFERENCES "customer"("customer_id")
);
DROP TABLE IF EXISTS "shipment_product";
CREATE TABLE IF NOT EXISTS "shipment_product" (
	"shipment_product_id"	INTEGER,
	"shipment_id"	INTEGER,
	"product_id"	INTEGER,
	"noteDetail"	TEXT,
	PRIMARY KEY("shipment_product_id" AUTOINCREMENT),
	FOREIGN KEY("shipment_id") REFERENCES "shipment"("shipment_id"),
	FOREIGN KEY("product_id") REFERENCES "product"("product_id")
);
DROP TABLE IF EXISTS "rma_status";
CREATE TABLE IF NOT EXISTS "rma_status" (
	"status_id"	INTEGER,
	"status_name"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("status_id" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "rma";
CREATE TABLE IF NOT EXISTS "rma" (
	"rma_id"	INTEGER,
	"customer_id"	INTEGER,
	"status_id"	INTEGER,
	"request_date"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	"resolution_date"	TIMESTAMP,
	"notes"	TEXT,
	PRIMARY KEY("rma_id" AUTOINCREMENT),
	FOREIGN KEY("customer_id") REFERENCES "customer"("customer_id"),
	FOREIGN KEY("status_id") REFERENCES "rma_status"("status_id")
);
DROP TABLE IF EXISTS "rma_product";
CREATE TABLE IF NOT EXISTS "rma_product" (
	"rma_product_id"	INTEGER,
	"rma_id"	INTEGER,
	"product_id"	INTEGER,
	"return_reason"	TEXT,
	"replacement_product_id"	INTEGER,
	"issue_category"	TEXT,
	"handling_method"	TEXT,
	"status"	TEXT DEFAULT '未處理',
	PRIMARY KEY("rma_product_id" AUTOINCREMENT),
	FOREIGN KEY("product_id") REFERENCES "product"("product_id"),
	FOREIGN KEY("replacement_product_id") REFERENCES "product"("product_id"),
	FOREIGN KEY("rma_id") REFERENCES "rma"("rma_id")
);
DROP TABLE IF EXISTS "product_sku";
CREATE TABLE IF NOT EXISTS "product_sku" (
	"sku_id"	INTEGER,
	"ean_code"	TEXT NOT NULL UNIQUE,
	"upc_code"	TEXT,
	"category_id"	INTEGER,
	"model_name"	TEXT,
	"product_name"	TEXT,
	"created_date"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("sku_id" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "product";
CREATE TABLE IF NOT EXISTS "product" (
	"product_id"	INTEGER,
	"sku_id"	INTEGER,
	"erp_no"	TEXT,
	"product_sn"	TEXT NOT NULL UNIQUE,
	"manufacturing_date"	TIMESTAMP,
	"created_date"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	"creator"	INTEGER,
	PRIMARY KEY("product_id" AUTOINCREMENT)
);
COMMIT;
