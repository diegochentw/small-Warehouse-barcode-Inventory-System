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
	FOREIGN KEY("product_id") REFERENCES "product"("product_id"),
	FOREIGN KEY("shipment_id") REFERENCES "shipment"("shipment_id")
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
	FOREIGN KEY("status_id") REFERENCES "rma_status"("status_id"),
	FOREIGN KEY("customer_id") REFERENCES "customer"("customer_id")
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
	FOREIGN KEY("rma_id") REFERENCES "rma"("rma_id"),
	FOREIGN KEY("product_id") REFERENCES "product"("product_id"),
	FOREIGN KEY("replacement_product_id") REFERENCES "product"("product_id")
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
INSERT INTO "user" ("user_id","username","password") VALUES (1,'diego','scrypt:32768:8:1$EIvn3Vz1vPMt481t$f951df94f80e1d560ed362d69de0f94cc358948e5bb0de8dd6de6c2ef12daaf4a60a3e0a8af0c3b95da41d952662adf465f1a945c0d2976f22fad701fee442ae');
INSERT INTO "user" ("user_id","username","password") VALUES (2,'test','scrypt:32768:8:1$WaEnhmEzIrKnOlpA$c1f5ee019dfa5e5b29cd19e8eaaad413da9e447a8bcd739d85e83be8d75c45cbf585df0db7576c65294db722e06291d69aa4f2cfb2d970630b8589557779d411');
INSERT INTO "category" ("category_id","category_name") VALUES (1,'電源供應器');
INSERT INTO "category" ("category_id","category_name") VALUES (2,'水冷');
INSERT INTO "category" ("category_id","category_name") VALUES (3,'空冷');
INSERT INTO "category" ("category_id","category_name") VALUES (4,'機殼');
INSERT INTO "category" ("category_id","category_name") VALUES (5,'音響');
INSERT INTO "category" ("category_id","category_name") VALUES (6,'其他周邊');
INSERT INTO "customer" ("customer_id","customer_name","contact","type","phone","email","address","created_date","notes") VALUES (1,'方美方','None','代理商','03-5264095','fm277@ms13.hinet.net','新竹市西雅里14鄰民富街251號','2009-10-06 06:09:03','方美方同時為供應商及客戶，過往長期發生客戶提供序號後即要求換新品，請務必注意序號的出廠日期起算');
INSERT INTO "customer" ("customer_id","customer_name","contact","type","phone","email","address","created_date","notes") VALUES (2,'PCHome','蕭國祥','代理商','02-27000898','alfiehsiao@staff.pchome.com.tw','台北市大安區敦化南路二段105號12樓',NULL,'None');
INSERT INTO "customer" ("customer_id","customer_name","contact","type","phone","email","address","created_date","notes") VALUES (3,'MOMO','None','電商','None','None','None',NULL,'富邦');
INSERT INTO "customer" ("customer_id","customer_name","contact","type","phone","email","address","created_date","notes") VALUES (4,'蝦皮','蔡馥彌','電商','02-66366559','aisa.tsai@shopee.com','台北市信義區菸廠路88號','2019-10-06 06:09:03',NULL);
INSERT INTO "customer" ("customer_id","customer_name","contact","type","phone","email","address","created_date","notes") VALUES (6,'Diego','陳學翰','RMA維修客人','935531547','diego_chen@enermax.com.tw','桃園市桃園區經國路888號2F之1','2023-10-06 06:09:03','優質顧客');
INSERT INTO "customer" ("customer_id","customer_name","contact","type","phone","email","address","created_date","notes") VALUES (7,'Evil','黃先生','RMA維修客人','9878177818','unknown@enermax.com.tw','','2023-10-06 06:09:03','奧客');
INSERT INTO "customer" ("customer_id","customer_name","contact","type","phone","email","address","created_date","notes") VALUES (14,'酷澎','韓先生','電商','03-3161675 #888','mis@enermax.com.tw','經國路888號2樓-1','2023-10-23 02:25:57','合作於 2023/10');
INSERT INTO "customer" ("customer_id","customer_name","contact","type","phone","email","address","created_date","notes") VALUES (16,'Jennifer','Mina','RMA維修客人','912345678','test@test.com','桃園市巾幗路88號','2023-10-26 08:17:37','退貨頻率極高');
INSERT INTO "shipment" ("shipment_id","type","category_id","customer_id","note","created_date") VALUES (1,'進倉',8,6,'','2023-10-31 08:23:44');
INSERT INTO "shipment_product" ("shipment_product_id","shipment_id","product_id","noteDetail") VALUES (1,1,8,NULL);
INSERT INTO "product_sku" ("sku_id","ean_code","upc_code","category_id","model_name","product_name","created_date") VALUES (2,'4713157727275','819315027271',1,'ERA1000EWT','ERVOLUTION D.F.2 1000','2023-10-27 08:08:53');
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (8,2,'AR00810400','2311110080700','2023-04-05 00:00:00','2023-10-31 02:45:23',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (9,2,'AR00810400','2311110080701','2022-02-02 00:00:00','2023-10-31 06:22:29',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (10,2,'AR00810400','2311110080702','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (11,2,'AR00810400','2311110080703','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (12,2,'AR00810400','2311110080704','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (13,2,'AR00810400','2311110080705','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (14,2,'AR00810400','2311110080706','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (15,2,'AR00810400','2311110080707','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (16,2,'AR00810400','2311110080708','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (17,2,'AR00810400','2311110080709','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (18,2,'AR00810400','2311110080710','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (19,2,'AR00810400','2311110080711','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (20,2,'AR00810400','2311110080712','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (21,2,'AR00810400','2311110080713','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (22,2,'AR00810400','2311110080714','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (23,2,'AR00810400','2311110080715','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (24,2,'AR00810400','2311110080716','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (25,2,'AR00810400','2311110080717','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (26,2,'AR00810400','2311110080718','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (27,2,'AR00810400','2311110080719','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (28,2,'AR00810400','2311110080720','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (29,2,'AR00810400','2311110080721','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (30,2,'AR00810400','2311110080722','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (31,2,'AR00810400','2311110080723','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (32,2,'AR00810400','2311110080724','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (33,2,'AR00810400','2311110080725','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (34,2,'AR00810400','2311110080726','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (35,2,'AR00810400','2311110080727','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (36,2,'AR00810400','2311110080728','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (37,2,'AR00810400','2311110080729','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (38,2,'AR00810400','2311110080730','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (39,2,'AR00810400','2311110080731','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (40,2,'AR00810400','2311110080732','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (41,2,'AR00810400','2311110080733','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (42,2,'AR00810400','2311110080734','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (43,2,'AR00810400','2311110080735','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (44,2,'AR00810400','2311110080736','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (45,2,'AR00810400','2311110080737','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (46,2,'AR00810400','2311110080738','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (47,2,'AR00810400','2311110080739','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (48,2,'AR00810400','2311110080740','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (49,2,'AR00810400','2311110080741','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (50,2,'AR00810400','2311110080742','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (51,2,'AR00810400','2311110080743','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (52,2,'AR00810400','2311110080744','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (53,2,'AR00810400','2311110080745','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (54,2,'AR00810400','2311110080746','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (55,2,'AR00810400','2311110080747','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (56,2,'AR00810400','2311110080748','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (57,2,'AR00810400','2311110080749','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (58,2,'AR00810400','2311110080750','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (59,2,'AR00810400','2311110080751','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (60,2,'AR00810400','2311110080752','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (61,2,'AR00810400','2311110080753','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (62,2,'AR00810400','2311110080754','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (63,2,'AR00810400','2311110080755','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (64,2,'AR00810400','2311110080756','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (65,2,'AR00810400','2311110080757','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (66,2,'AR00810400','2311110080758','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (67,2,'AR00810400','2311110080759','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (68,2,'AR00810400','2311110080760','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (69,2,'AR00810400','2311110080761','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (70,2,'AR00810400','2311110080762','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (71,2,'AR00810400','2311110080763','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (72,2,'AR00810400','2311110080764','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (73,2,'AR00810400','2311110080765','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (74,2,'AR00810400','2311110080766','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (75,2,'AR00810400','2311110080767','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (76,2,'AR00810400','2311110080768','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (77,2,'AR00810400','2311110080769','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (78,2,'AR00810400','2311110080770','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (79,2,'AR00810400','2311110080771','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (80,2,'AR00810400','2311110080772','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (81,2,'AR00810400','2311110080773','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (82,2,'AR00810400','2311110080774','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (83,2,'AR00810400','2311110080775','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (84,2,'AR00810400','2311110080776','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (85,2,'AR00810400','2311110080777','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (86,2,'AR00810400','2311110080778','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (87,2,'AR00810400','2311110080779','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (88,2,'AR00810400','2311110080780','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (89,2,'AR00810400','2311110080781','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (90,2,'AR00810400','2311110080782','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (91,2,'AR00810400','2311110080783','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (92,2,'AR00810400','2311110080784','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (93,2,'AR00810400','2311110080785','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (94,2,'AR00810400','2311110080786','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (95,2,'AR00810400','2311110080787','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (96,2,'AR00810400','2311110080788','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (97,2,'AR00810400','2311110080789','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (98,2,'AR00810400','2311110080790','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (99,2,'AR00810400','2311110080791','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (100,2,'AR00810400','2311110080792','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (101,2,'AR00810400','2311110080793','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (102,2,'AR00810400','2311110080794','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (103,2,'AR00810400','2311110080795','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (104,2,'AR00810400','2311110080796','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (105,2,'AR00810400','2311110080797','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (106,2,'AR00810400','2311110080798','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
INSERT INTO "product" ("product_id","sku_id","erp_no","product_sn","manufacturing_date","created_date","creator") VALUES (107,2,'AR00810400','2311110080799','2022-02-02 00:00:00','2023-10-31 06:22:30',NULL);
COMMIT;
