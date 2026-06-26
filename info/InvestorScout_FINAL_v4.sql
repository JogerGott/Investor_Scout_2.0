-- =============================================================
-- INVESTOR SCOUT — DDL MySQL COMPLETO v4
-- Arquitectura: métricas separadas por frecuencia de actualización
-- Motor: MySQL 8.0+ / InnoDB
-- Encoding: utf8mb4
-- =============================================================

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- -------------------------------------------------------------
-- 1. CLIENTE
-- El inversor registrado. Raíz del sistema.
-- email UNIQUE: un solo acceso por persona.
-- password_hash: NUNCA texto plano. Usar bcrypt en app.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cliente (
    id_cliente      INT             NOT NULL AUTO_INCREMENT,
    nombre          VARCHAR(100)    NOT NULL,
    apellido        VARCHAR(100)    NOT NULL,
    email           VARCHAR(255)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL
                    COMMENT 'Hash bcrypt/argon2 — nunca texto plano',
    telefono        VARCHAR(20)         NULL,
    fecha_registro  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_cliente   PRIMARY KEY (id_cliente),
    CONSTRAINT uq_email     UNIQUE      (email)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Inversores registrados en la plataforma';


-- -------------------------------------------------------------
-- 2. PORTAFOLIO
-- Cuenta de inversión de un cliente.
-- cash: efectivo no invertido en ese portafolio.
-- ON DELETE RESTRICT: no se elimina cliente con portafolios.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS portafolio (
    id_portafolio       INT             NOT NULL AUTO_INCREMENT,
    id_cliente          INT             NOT NULL,
    nombre_portafolio   VARCHAR(150)    NOT NULL,
    perfil_riesgo       ENUM(
                            'CONSERVADOR',
                            'MODERADO',
                            'AGRESIVO'
                        )               NOT NULL DEFAULT 'MODERADO',
    cash                DECIMAL(20,2)   NOT NULL DEFAULT 0.00
                        COMMENT 'Efectivo disponible en USD',
    fecha_creacion      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_portafolio    PRIMARY KEY (id_portafolio),
    CONSTRAINT fk_portafolio_cliente  FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    INDEX idx_portafolio_cliente (id_cliente)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Cuentas de inversión por cliente';

-- -----------------------------------------------------------
-- TABLA 3: METRICAS_PORTAFOLIO
-- Histórico de métricas de performance por portafolio y fecha.
-- PK compuesta (id_portafolio, fecha_calculo):
--   permite un registro por día, preservando el histórico.
-- ON DELETE CASCADE: si el portafolio se elimina, se elimina
--   su historial de métricas (datos dependientes).
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS metricas_portafolio (
    id_portafolio       INT             NOT NULL,
    fecha_calculo       DATE            NOT NULL,
    retorno_total       DECIMAL(8,4)       NULL   COMMENT 'Retorno acumulado %',
    volatilidad         DECIMAL(8,4)       NULL   COMMENT 'Desviación estándar de retornos',
    sharpe              DECIMAL(8,4)       NULL   COMMENT 'Ratio de Sharpe',
    max_drawdown        DECIMAL(8,4)       NULL   COMMENT 'Máxima caída desde pico %',
    beta                DECIMAL(6,4)       NULL   COMMENT 'Sensibilidad relativa al mercado',
    alpha               DECIMAL(8,4)       NULL   COMMENT 'Exceso de retorno vs benchmark',
    correlacion         DECIMAL(5,4)       NULL   COMMENT 'Correlación vs benchmark',
    standard_deviation   DECIMAL(12,6)       NULL   COMMENT 'Desviación estándar del portafolio',

    CONSTRAINT pk_metricas_portafolio  PRIMARY KEY (id_portafolio, fecha_calculo),
    CONSTRAINT fk_metmetricas_port  FOREIGN KEY (id_portafolio)
        REFERENCES portafolio (id_portafolio)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Histórico diario de métricas de performance por portafolio';

-- -------------------------------------------------------------
-- 4. SNAPSHOT_PORTAFOLIO
-- Fotografía diaria del valor total del portafolio.
-- Permite graficar la curva de evolución en el tiempo.
-- UNIQUE (id_portafolio, fecha_snapshot): un snapshot por día.
-- ON DELETE CASCADE: se elimina con el portafolio.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS snapshot_portafolio (
    id_snapshot             INT             NOT NULL AUTO_INCREMENT,
    id_portafolio           INT             NOT NULL,
    fecha_snapshot          DATE            NOT NULL,
    cash                    DECIMAL(20,2)       NULL COMMENT 'Efectivo en esa fecha',
    inversion_total         DECIMAL(20,2)       NULL COMMENT 'Total invertido (costo base)',
    valor_total             DECIMAL(20,2)       NULL COMMENT 'Valor de mercado total',
    unrealized_pnl          DECIMAL(20,2)       NULL COMMENT 'P&L no realizado total',
    retorno_total           DECIMAL(8,4)       NULL COMMENT 'Retorno acumulado %',

    CONSTRAINT pk_snapshot_port         PRIMARY KEY (id_snapshot),
    CONSTRAINT fk_snapshot_port_portafolio    FOREIGN KEY (id_portafolio)
        REFERENCES portafolio (id_portafolio)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_snapshot_port_fecha   UNIQUE (id_portafolio, fecha_snapshot),

    INDEX idx_snapshot_port_fecha (fecha_snapshot)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Histórico diario del valor total del portafolio';


-- -------------------------------------------------------------
-- 5. ACTIVO
-- Catálogo de instrumentos financieros.
-- ticker UNIQUE: no pueden existir dos AAPL.
-- tipo_activo: discriminador ISA → EQUITY o BOND.
-- Aquí NO hay precio ni ratios — esos viven en tablas propias.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activo (
    id_activo       INT             NOT NULL AUTO_INCREMENT,
    ticker          VARCHAR(20)     NOT NULL,
    nombre          VARCHAR(200)    NOT NULL,
    tipo_activo     ENUM(
                        'EQUITY',
                        'BOND'
                    )               NOT NULL COMMENT 'Discriminador ISA',
    moneda          VARCHAR(3)      NOT NULL DEFAULT 'USD'
                    COMMENT 'ISO 4217',
    exchange        VARCHAR(50)         NULL COMMENT 'NYSE, NASDAQ, BMV...',
    pais            VARCHAR(100)        NULL,

    CONSTRAINT pk_activo    PRIMARY KEY (id_activo),
    CONSTRAINT uq_ticker    UNIQUE      (ticker),

    INDEX idx_activo_tipo (tipo_activo)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Catálogo de instrumentos financieros';


-- -------------------------------------------------------------
-- 6. MOVIMIENTO
-- Registro INMUTABLE de cada transacción BUY/SELL.
-- Equivalente en BD de la LinkedList de Python.
-- PK simple AUTO_INCREMENT: permite múltiples compras del
-- mismo activo sin colisión de PK.
-- ON DELETE RESTRICT: protege la integridad del historial.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movimiento (
    id_movimiento       INT             NOT NULL AUTO_INCREMENT,
    id_portafolio       INT             NOT NULL,
    id_activo           INT             NOT NULL,
    tipo_mov            ENUM(
                            'BUY',
                            'SELL'
                        )               NOT NULL,
    cantidad            DECIMAL(18,8)   NOT NULL COMMENT 'Número de acciones',
    precio_por_accion   DECIMAL(18,6)   NOT NULL COMMENT 'Precio unitario al momento',
    fee                 DECIMAL(18,6)   NOT NULL DEFAULT 0.000000
                        COMMENT 'Comisión del bróker',
    notas               TEXT                NULL
                        COMMENT '¿Por qué se realizó esta operación?',
    fecha_transaccion   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_movimiento    PRIMARY KEY (id_movimiento),
    CONSTRAINT fk_movimiento_port      FOREIGN KEY (id_portafolio)
        REFERENCES portafolio (id_portafolio)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_movimiento_activo    FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    INDEX idx_mov_portafolio    (id_portafolio),
    INDEX idx_mov_activo        (id_activo),
    INDEX idx_mov_fecha         (fecha_transaccion)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Historial inmutable de transacciones — LinkedList en BD';


-- -------------------------------------------------------------
-- 7. POSICION
-- Estado ACTUAL de un activo dentro de un portafolio.
-- PK compuesta (id_portafolio, id_activo): resuelve el N:N.
-- costo_base: precio promedio ponderado, recalculado desde
-- MOVIMIENTO al ejecutar cada operación.
-- ON DELETE CASCADE en portafolio, RESTRICT en activo.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS posicion (
    id_portafolio           INT             NOT NULL,
    id_activo               INT             NOT NULL,
    posicion_actual         DECIMAL(18,8)   NOT NULL DEFAULT 0.00000000
                            COMMENT 'Shares actuales en cartera',
    costo_base              DECIMAL(18,6)   NOT NULL DEFAULT 0.000000
                            COMMENT 'Precio promedio ponderado de compra',
    valor_mercado           DECIMAL(20,2)       NULL
                            COMMENT 'posicion_actual × precio_mercado',
    unrealized_pnl          DECIMAL(20,2)       NULL
                            COMMENT 'Ganancia/pérdida no realizada',
    daily_pnl               DECIMAL(20,2)       NULL
                            COMMENT 'Ganancia/pérdida del día',
    fecha_adquisicion       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                            COMMENT 'Primera compra de este activo',
    ultima_actualizacion    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_posicion      PRIMARY KEY (id_portafolio, id_activo),
    CONSTRAINT fk_posicion_port      FOREIGN KEY (id_portafolio)
        REFERENCES portafolio (id_portafolio)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_posicion_activo    FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Posición activa actual por portafolio y activo';


-- -------------------------------------------------------------
-- 8. SNAPSHOT_POSICION
-- Fotografía diaria de cada posición individual.
-- Permite responder: "¿cómo estaba mi AAPL hace 3 meses?"
-- UNIQUE (id_portafolio, id_activo, fecha_snapshot):
-- un snapshot por activo por portafolio por día.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS snapshot_posicion (
    id_snapshot         INT             NOT NULL AUTO_INCREMENT,
    id_portafolio       INT             NOT NULL,
    id_activo           INT             NOT NULL,
    fecha_snapshot      DATE            NOT NULL,
    posicion_actual     DECIMAL(18,8)   NOT NULL COMMENT 'Shares en esa fecha',
    precio_cierre       DECIMAL(18,6)   NOT NULL COMMENT 'Precio de cierre',
    costo_base          DECIMAL(18,6)   NOT NULL COMMENT 'Costo promedio en esa fecha',
    valor_mercado       DECIMAL(20,2)   NOT NULL COMMENT 'Valor de la posición',
    unrealized_pnl      DECIMAL(20,2)   NOT NULL COMMENT 'P&L no realizado',
    change_pct          DECIMAL(8,4)       NULL COMMENT 'Variación % del día',

    CONSTRAINT pk_snapshot          PRIMARY KEY (id_snapshot),
    CONSTRAINT fk_snapshotposi_port      FOREIGN KEY (id_portafolio)
        REFERENCES portafolio (id_portafolio)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_snapshotposi_act       FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT uq_snapshotposi_fecha    UNIQUE (id_portafolio, id_activo, fecha_snapshot),

    INDEX idx_snapshotposi_fecha (fecha_snapshot)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Histórico diario del estado de cada posición individual';


-- -------------------------------------------------------------
-- 9. MARKET_METRICS  ← actualización DIARIA
-- Métricas de valuación dependientes del precio de mercado.
-- Una fila por activo por fecha — NUNCA se sobreescribe,
-- siempre se inserta. Así no se pierde el histórico.
-- Origen: Yahoo Finance precio en tiempo real.
-- UNIQUE (id_activo, fecha): una métrica por día por activo.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metricas_mercado (
    id_metricas           INT             NOT NULL AUTO_INCREMENT,
    id_activo           INT             NOT NULL,
    fecha               DATE            NOT NULL,
    precio              DECIMAL(18,6)       NULL COMMENT 'Precio de cierre',
    market_cap          BIGINT              NULL COMMENT 'Capitalización en USD',
    enterprise_value    BIGINT              NULL COMMENT 'EV = market cap + deuda - caja',
    pe_ratio            DECIMAL(10,2)       NULL COMMENT 'Price to Earnings (trailing)',
    pe_forward          DECIMAL(10,2)       NULL COMMENT 'P/E forward (estimado)',
    pb_ratio            DECIMAL(10,4)       NULL COMMENT 'Price to Book',
    ps_ratio            DECIMAL(10,4)       NULL COMMENT 'Price to Sales',
    peg                 DECIMAL(10,4)       NULL COMMENT 'Price/Earnings to Growth',
    beta                DECIMAL(5,2)        NULL COMMENT 'Volatilidad relativa al mercado',
    dividend_yield      DECIMAL(8,4)        NULL COMMENT 'Rendimiento por dividendos %',

    CONSTRAINT pk_metricas_mercado    PRIMARY KEY (id_metricas),
    CONSTRAINT fk_metricasmercado_activo       FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_metricasmercado_fecha        UNIQUE (id_activo, fecha),

    INDEX idx_metricas_mercado_fecha (fecha)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Métricas de valuación diarias por activo (dependen del precio)';


-- -------------------------------------------------------------
-- 10. FINANCIAL_RATIOS  ← actualización TRIMESTRAL
-- Ratios derivados de estados financieros.
-- Se insertan cuando la empresa publica resultados (earnings).
-- Origen: 10-Q y 10-K procesados por el agente RAG.
-- periodo: 'Q1 2024', 'Q2 2024', 'FY 2023', etc.
-- UNIQUE (id_activo, periodo): un ratio por periodo.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ratios_financieros (
    id_ratio            INT             NOT NULL AUTO_INCREMENT,
    id_activo           INT             NOT NULL,
    periodo             VARCHAR(10)     NOT NULL COMMENT 'Q1 2024, FY 2023, etc.',
    fecha_reporte       DATE            NOT NULL COMMENT 'Fecha de publicación',
    
    roe                 DECIMAL(8,4)       NULL COMMENT 'Return on Equity',
    roa                 DECIMAL(8,4)       NULL COMMENT 'Return on Assets',
    roic                DECIMAL(8,4)       NULL COMMENT 'Return on Invested Capital',
    
    ev_ebitda           DECIMAL(10,2)        NULL COMMENT 'Enterprise Value to EBITDA',
    
    gross_margin        DECIMAL(8,4)       NULL COMMENT 'Margen bruto %',
    operating_margin    DECIMAL(8,4)       NULL COMMENT 'Margen operativo %',
    net_margin          DECIMAL(8,4)       NULL COMMENT 'Margen neto %',
    
    quick_ratio         DECIMAL(8,4)       NULL COMMENT 'Liquidez inmediata',
    current_ratio       DECIMAL(8,4)       NULL COMMENT 'Liquidez corriente',
    debt_equity         DECIMAL(10,4)       NULL COMMENT 'Deuda / Equity (D/E)',
    icr                 DECIMAL(8,4)     NULL COMMENT 'Interest coverage ratio (ICR)',
    asset_turnover      DECIMAL(8,4)     NULL COMMENT 'Revenue / Average Total Assets',
    
    eps                 DECIMAL(14,4)       NULL COMMENT 'Earnings Per Share',
    eps_growth          DECIMAL(8,4)       NULL COMMENT 'Crecimiento EPS YoY %',
    revenue_growth      DECIMAL(8,4)       NULL COMMENT 'Crecimiento ingresos YoY %',
    fcf_yield           DECIMAL(8,4)       NULL COMMENT 'Free Cash Flow Yield %',

    CONSTRAINT pk_ratio    PRIMARY KEY (id_ratio),
    CONSTRAINT fk_ratiosfin_activo   FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_ratiosfin_periodo  UNIQUE (id_activo, periodo, fecha_reporte),

    INDEX idx_ratiosfin_fecha (fecha_reporte)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Ratios financieros trimestrales por activo';


-- -------------------------------------------------------------
-- 11. INCOME_STATEMENT  ← actualización TRIMESTRAL
-- Estado de resultados. Los números crudos, no los ratios.
-- El agente RAG extrae estos valores de los 10-Q / 10-K.
-- UNIQUE (id_activo, periodo): un estado por periodo.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS income_statement (
    id_statement        INT             NOT NULL AUTO_INCREMENT,
    id_activo           INT             NOT NULL,
    periodo             VARCHAR(10)     NOT NULL COMMENT 'Q1 2024, FY 2023, etc.',
    fecha_reporte       DATE            NOT NULL,
    revenue             DECIMAL(20,2)       NULL COMMENT 'Ingresos totales',
    cost_of_revenue     DECIMAL(20,2)       NULL COMMENT 'Costo de ventas',
    gross_profit        DECIMAL(20,2)       NULL COMMENT 'Ganancia bruta',
    operating_expenses  DECIMAL(20,2)       NULL COMMENT 'Gastos operativos',
    operating_income    DECIMAL(20,2)       NULL COMMENT 'EBIT',
    net_income          DECIMAL(20,2)       NULL COMMENT 'Ganancia neta',
    ebitda              DECIMAL(20,2)       NULL COMMENT 'EBITDA',
    shares_outstanding  BIGINT              NULL COMMENT 'Acciones en circulación',
    interest_expense    DECIMAL(20,2)       NULL COMMENT 'Gastos por intereses',
    tax_expense         DECIMAL(20,2)       NULL COMMENT 'Gastos por impuestos',


    CONSTRAINT pk_statement        PRIMARY KEY (id_statement),
    CONSTRAINT fk_incomestate_activo    FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_incomestate_periodo   UNIQUE (id_activo, periodo),

    INDEX idx_incomestate_fecha (fecha_reporte)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Estado de resultados trimestral por activo';


-- -------------------------------------------------------------
-- 12. BALANCE_SHEET  ← actualización TRIMESTRAL
-- Balance general. Activos, pasivos y patrimonio.
-- Crítico para calcular D/E, Book Value, y el modelo DCF.
-- UNIQUE (id_activo, periodo): un balance por periodo.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS balance_sheet (
    id_balance          INT             NOT NULL AUTO_INCREMENT,
    id_activo           INT             NOT NULL,
    periodo             VARCHAR(10)     NOT NULL COMMENT 'Q1 2024, FY 2023, etc.',
    fecha_reporte       DATE            NOT NULL,
    total_assets        DECIMAL(20,2)       NULL COMMENT 'Activos totales',
    total_liabilities   DECIMAL(20,2)       NULL COMMENT 'Pasivos totales',
    total_equity        DECIMAL(20,2)       NULL COMMENT 'Patrimonio neto',
    total_debt          DECIMAL(20,2)       NULL COMMENT 'Deuda total (corto + largo plazo)',
    cash_equivalents    DECIMAL(20,2)       NULL COMMENT 'Caja y equivalentes',
    current_assets      DECIMAL(20,2)       NULL COMMENT 'Activos corrientes',
    current_liabilities DECIMAL(20,2)       NULL COMMENT 'Pasivos corrientes',

    CONSTRAINT pk_balance     PRIMARY KEY (id_balance),
    CONSTRAINT fk_balancesheet_activo    FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_balance_she_periodo   UNIQUE (id_activo, periodo),

    INDEX idx_balancesheet_fecha (fecha_reporte)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Balance general trimestral por activo';


-- -------------------------------------------------------------
-- 13. CASH_FLOW  ← actualización TRIMESTRAL
-- Flujo de caja. El más crítico para el modelo DCF.
-- Free Cash Flow = Operating CF - Capex.
-- El agente RAG extrae estos valores de los 10-Q / 10-K.
-- UNIQUE (id_activo, periodo): un flujo por periodo.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cash_flow (
    id_cashflow         INT             NOT NULL AUTO_INCREMENT,
    id_activo           INT             NOT NULL,
    periodo             VARCHAR(10)     NOT NULL COMMENT 'Q1 2024, FY 2023, etc.',
    fecha_reporte       DATE            NOT NULL,
    operating_cf        DECIMAL(20,4)       NULL COMMENT 'Flujo operativo',
    investing_cf        DECIMAL(20,4)       NULL COMMENT 'Flujo de inversión',
    financing_cf        DECIMAL(20,4)       NULL COMMENT 'Flujo de financiamiento',
    free_cash_flow      DECIMAL(20,4)       NULL COMMENT 'FCF = Operating CF - Capex',
    capex               DECIMAL(20,4)       NULL COMMENT 'Gastos de capital',

    CONSTRAINT pk_cashflow      PRIMARY KEY (id_cashflow),
    CONSTRAINT fk_cash_flow_activo     FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_cash_flow_periodo    UNIQUE (id_activo, periodo),

    INDEX idx_cash_flow_fecha (fecha_reporte)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Flujo de caja trimestral por activo — base del modelo DCF';


-- -------------------------------------------------------------
-- 14. HISTORICO
-- Serie temporal OHLCV de precios por activo.
-- PK compuesta (id_activo, fecha): un precio por día.
-- Diferente de MARKET_METRICS: este es el precio histórico
-- puro para velas y retornos históricos.
-- ON DELETE CASCADE: se elimina con el activo.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS historico (
    id_activo   INT             NOT NULL,
    fecha       DATE            NOT NULL,
    open_price  DECIMAL(18,6)       NULL,
    high_price  DECIMAL(18,6)       NULL,
    low_price   DECIMAL(18,6)       NULL,
    close_price DECIMAL(18,6)   NOT NULL,
    adjust_close DECIMAL(18,6)   NOT NULL COMMENT 'Precio de cierre ajustado',
    volumen     BIGINT              NULL,

    CONSTRAINT pk_historico     PRIMARY KEY (id_activo, fecha),
    CONSTRAINT fk_hist_activo   FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    INDEX idx_hist_fecha (fecha)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Precios históricos OHLCV por activo';


-- -------------------------------------------------------------
-- 15. EQUITY  — subtipo ISA de ACTIVO
-- Solo existe si activo.tipo_activo = 'EQUITY'.
-- Guarda campos estáticos o de baja frecuencia específicos
-- de acciones: sector, industria, próxima earnings date.
-- Los ratios y precios viven en sus propias tablas.
-- ON DELETE CASCADE: se elimina con su activo padre.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS equity (
    id_activo       INT             NOT NULL,
    sector          VARCHAR(100)        NULL,
    industria       VARCHAR(150)        NULL,
    earnings_date   DATE                NULL
                    COMMENT 'Próxima fecha de reporte de resultados',

    CONSTRAINT pk_equity        PRIMARY KEY (id_activo),
    CONSTRAINT fk_equity_activo     FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Datos estáticos de acciones — subtipo ISA de ACTIVO';


-- -------------------------------------------------------------
-- 16. BOND  — subtipo ISA de ACTIVO
-- Solo existe si activo.tipo_activo = 'BOND'.
-- Datos específicos de instrumentos de renta fija.
-- ON DELETE CASCADE: se elimina con su activo padre.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bond (
    id_activo           INT             NOT NULL,
    fecha_maduracion    DATE                NULL COMMENT 'Fecha de vencimiento',
    tasa_cupon          DECIMAL(8,4)        NULL COMMENT 'Tasa anual del cupón',
    frecuencia_pago     ENUM(
                            'MENSUAL',
                            'TRIMESTRAL',
                            'SEMESTRAL',
                            'ANUAL'
                        )                   NULL,
    valor_nominal       DECIMAL(20,2)       NULL COMMENT 'Valor par del bono',
    calificacion        VARCHAR(20)         NULL COMMENT 'AAA, AA+, BBB-...',
    emisor              ENUM(
                            'SOBERANO',
                            'CORPORATIVO'
                        )               NOT NULL,

    CONSTRAINT pk_bond          PRIMARY KEY (id_activo),
    CONSTRAINT fk_bond_activo   FOREIGN KEY (id_activo)
        REFERENCES activo (id_activo)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Datos específicos de bonos — subtipo ISA de ACTIVO';

-- -------------------------------------------------------------
-- 17. benchmark 
-- -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS benchmark (
    id_benchmark  INT NOT NULL AUTO_INCREMENT,
    ticker        VARCHAR(100) NOT NULL COMMENT 'Ticker del benchmark',
    nombre        VARCHAR(200) NOT NULL COMMENT 'Nombre descriptivo del índice',  

    CONSTRAINT  pk_benchmark    PRIMARY KEY(id_benchmark),
    CONSTRAINT unico_ticker UNIQUE (ticker)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Indice sado para comparar el rendimineto del portafolio';



SET FOREIGN_KEY_CHECKS = 1;


-- =============================================================
-- RESUMEN EJECUTIVO DE LA ARQUITECTURA v4
-- =============================================================
--
-- TABLAS: 17 en total
-- RELACIONES FK: 17
--
-- DECISIÓN ARQUITECTÓNICA PRINCIPAL:
-- La antigua tabla EQUITY, que almacenaba información estática,
-- precios, métricas de mercado y ratios financieros, se divide
-- en tablas especializadas según el origen y la frecuencia de
-- actualización de los datos:
--
--   METRICAS_MERCADO   → diaria       → Yahoo Finance
--   RATIOS_FINANCIEROS → trimestral   → Yahoo Finance + métricas derivadas
--   ESTADO_RESULTADOS  → trimestral   → Yahoo Finance
--   BALANCE_GENERAL    → trimestral   → Yahoo Finance
--   FLUJO_CAJA         → trimestral   → Yahoo Finance
--   HISTORICO          → diaria       → Yahoo Finance (OHLCV)
--
-- EQUITY y BOND únicamente almacenan información específica
-- y de baja frecuencia de cambio para cada tipo de activo
-- (sector, industria, fecha estimada de resultados, cupón,
-- fecha de maduración, etc.).
--
-- Los datos dinámicos (precios, estados financieros, métricas
-- y ratios) se almacenan en tablas independientes para preservar
-- el histórico y facilitar su actualización.
--
-- VENTAJAS:
-- 1. Se preserva completamente el histórico mediante INSERT;
--    los datos históricos nunca se sobrescriben.
-- 2. Es posible consultar cualquier estado financiero o métrica
--    correspondiente a un periodo específico.
-- 3. Se separan claramente los datos fuente (Yahoo Finance) de
--    las métricas calculadas por el sistema.
-- 4. Los modelos financieros (DCF, análisis fundamental, etc.)
--    consumen directamente los estados financieros almacenados.
-- 5. La arquitectura es escalable; cada conjunto de datos crece
--    de forma independiente según su frecuencia de actualización.
--
-- CARDINALIDADES:
--
-- CLIENTE                 1:N   PORTAFOLIO
--
-- PORTAFOLIO              1:N   MOVIMIENTO
-- PORTAFOLIO              1:N   POSICION
-- PORTAFOLIO              1:N   SNAPSHOT_PORTAFOLIO
-- PORTAFOLIO              1:N   SNAPSHOT_POSICION
-- PORTAFOLIO              1:N   METRICAS_PORTAFOLIO
--
-- ACTIVO                  1:N   MOVIMIENTO
-- ACTIVO                  1:N   POSICION
-- ACTIVO                  1:N   SNAPSHOT_POSICION
-- ACTIVO                  1:N   HISTORICO
-- ACTIVO                  1:N   METRICAS_MERCADO
-- ACTIVO                  1:N   RATIOS_FINANCIEROS
-- ACTIVO                  1:N   ESTADO_RESULTADOS
-- ACTIVO                  1:N   BALANCE_GENERAL
-- ACTIVO                  1:N   FLUJO_CAJA
--
-- ACTIVO                  1:0..1 EQUITY       (ISA total disjoint)
-- ACTIVO                  1:0..1 BOND         (ISA total disjoint)
--
-- BENCHMARK               1:N   METRICAS_PORTAFOLIO (referencia lógica)
--
-- =============================================================