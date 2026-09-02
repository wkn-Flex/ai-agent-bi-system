-- ============================================================
-- Superstore 商业智能分析数据库建表脚本
-- 数据库：superstore_bi
-- 字符集：utf8mb4
-- 表数量：4张（customers, products, orders, order_items）
-- 生成日期：2026-09-02
-- ============================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS superstore_bi
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE superstore_bi;

-- ============================================================
-- 1. 客户表 customers
-- ============================================================
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id     VARCHAR(20)     NOT NULL COMMENT '客户编号，如CG-12520',
    segment         VARCHAR(20)     NOT NULL COMMENT '客户细分市场：Consumer/Corporate/Home Office',
    city            VARCHAR(50)     NOT NULL COMMENT '城市',
    state           VARCHAR(50)     NOT NULL COMMENT '州/省',
    region          VARCHAR(20)     NOT NULL COMMENT '地区：East/West/Central/South',
    country         VARCHAR(50)     NOT NULL DEFAULT 'United States' COMMENT '国家',
    PRIMARY KEY (customer_id),
    KEY idx_segment (segment),
    KEY idx_region (region),
    KEY idx_state (state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户信息表';

-- ============================================================
-- 2. 产品表 products
-- ============================================================
CREATE TABLE products (
    product_id      VARCHAR(30)     NOT NULL COMMENT '产品编号，如FUR-BO-10001798',
    product_name    VARCHAR(255)    NOT NULL COMMENT '产品名称',
    category        VARCHAR(30)     NOT NULL COMMENT '产品大类：Furniture/Office Supplies/Technology',
    sub_category    VARCHAR(30)     NOT NULL COMMENT '产品子类别，如Bookcases/Chairs/Labels等',
    PRIMARY KEY (product_id),
    KEY idx_category (category),
    KEY idx_sub_category (sub_category),
    KEY idx_product_name (product_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='产品信息表';

-- ============================================================
-- 3. 订单表 orders
-- ============================================================
CREATE TABLE orders (
    order_id        VARCHAR(30)     NOT NULL COMMENT '订单编号，如CA-2016-152156',
    order_date      DATE            NOT NULL COMMENT '下单日期',
    ship_date       DATE            NOT NULL COMMENT '发货日期',
    ship_mode       VARCHAR(20)     NOT NULL COMMENT '发货方式：Standard Class/Second Class/First Class/Same Day',
    customer_id     VARCHAR(20)     NOT NULL COMMENT '客户编号（外键→customers.customer_id）',
    PRIMARY KEY (order_id),
    KEY idx_order_date (order_date),
    KEY idx_customer_id (customer_id),
    KEY idx_ship_mode (ship_mode),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单主表';

-- ============================================================
-- 4. 订单项表 order_items
-- ============================================================
CREATE TABLE order_items (
    id              INT             NOT NULL AUTO_INCREMENT COMMENT '订单项自增ID',
    order_id        VARCHAR(30)     NOT NULL COMMENT '订单编号（外键→orders.order_id）',
    product_id      VARCHAR(30)     NOT NULL COMMENT '产品编号（外键→products.product_id）',
    sales           DECIMAL(12,4)  NOT NULL COMMENT '销售额（美元，含折扣后实际销售额）',
    quantity        INT             NOT NULL COMMENT '销售数量（件）',
    discount        DECIMAL(5,2)   NOT NULL DEFAULT 0.00 COMMENT '折扣率，0-0.8',
    profit          DECIMAL(12,4)  NOT NULL COMMENT '利润（美元，可为负）',
    PRIMARY KEY (id),
    KEY idx_order_id (order_id),
    KEY idx_product_id (product_id),
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders (order_id),
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单项明细表';

-- ============================================================
-- 验证：查看表结构
-- ============================================================
SHOW TABLES;
DESCRIBE customers;
DESCRIBE products;
DESCRIBE orders;
DESCRIBE order_items;
